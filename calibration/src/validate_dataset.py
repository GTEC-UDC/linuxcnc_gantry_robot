"""Check the correction model of the gantry with the RoboLoc-G dataset.

The correction model is fitted with the calibration capture. This script checks
how well it works with the RoboLoc-G dataset.

For each take of the RoboLoc-G dataset, the positions measured by OptiTrack are
compared with the commanded positions of the gantry. This is done twice:

- "before": with the commanded gantry positions.
- "after": with the commanded gantry positions corrected with the model, which
  should give approximately the "real" gantry positions.

The difference between the two results is what the correction improves.

First the OptiTrack positions are aligned with the gantry ones: they are shifted
in time, rotated and translated. The alignment is defined by a time shift, Euler
angle rotations in X, Y, Z, and displacements in X, Y, Z (see AlignmentTransform
in data.py).

The "before" alignment is fitted with the recorded gantry positions. The "after"
alignment with the corrected ones.

By default, the same two alignments are used with all the takes. They are fitted
with each take separately and then averaged. With --per-take-alignment, each
take uses the alignments fitted with it.

The alignments are always fitted with the rigid body of the z-axis platform of
the gantry ("Grua"), and then they are used with the other rigid bodies too.

Note that the following samples are excluded by default:

- The first seconds of each take (--skip-initial-s). The RoboLoc-G data missed
  some data at the start, so the first seconds are excluded.
- The samples in which OptiTrack is farther than a threshold from the gantry
  (--dropout-mm). They are considered tracking errors of OptiTrack.
"""

import argparse
import logging
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, TypedDict

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy as scp
from data import (
    AlignmentTransform,
    CorrectionModel,
    interp_columns,
    load_correction,
    load_optitrack_data,
    load_optitrack_metadata,
    samples_mse,
)
from defaults import CALIBRATION_FILE, DATASET_DIR

logger = logging.getLogger("validate_dataset")

# Folders of the dataset with the OptiTrack recordings and with the gantry positions
OPTITRACK_DIR = DATASET_DIR / "OPTITRACK_MEASUREMENTS_CSV"
GROUND_TRUTH_DIR = DATASET_DIR / "GROUND_TRUTH"

# Settings of the alignment fit
ROT_CENTER = (0.0, 0.0, 1500.0)
Z_ROT_GUESS = -1.6520  # rad (-94.66 degrees), initial guess of the rotation about z
MAX_ROT = 0.15  # rad, max rotation for the alignment optimization

# Default values of the command line options (see parse_args)
TAKES = ["circle", "random1", "random2", "zigzag1", "zigzag2", "zigzag3", "zigzag4"]
BODIES = ["Grua", "UWB_tag", "FTM_tag", "Feet"]  # rigid bodies tracked by OptiTrack
FRAME_BODY = "Grua"  # rigid body of the gantry, used to fit the alignments
DROPOUT_MM = 15.0  # mm, samples farther than this from the gantry are left out
SKIP_INITIAL_S = 6.0  # s, time at the start of each take that is left out
SENS_THRESHOLDS = [1e9, 200, 100, 50, 30, 20, 15]  # mm, see --sensitivity-thresholds

XYZ = ["x", "y", "z"]

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]

# Gantry positions to compare
Target = Literal["corrected", "uncorrected"]


class AlignmentResult(TypedDict):
    """Result of the residuals of one OptiTrack rigid body of a take."""

    rmse: float
    median: float
    p95: float
    n: int  # number of samples
    n_drop: int  # number of samples excluded as tracking errors
    alignment: AlignmentTransform  # alignment used
    resid: FloatArray  # residual of the samples kept (3D distance)
    rvec: FloatArray  # residual of the samples kept (one x, y ,z row per sample)
    rmax: float  # largest residual of the samples kept
    r_all: FloatArray  # residual of all the samples of the take (3D distance)
    valid: BoolArray  # bool array indicating samples kept


class TakeResult(TypedDict):
    """Results of the rigid bodies of a take."""

    take: str
    # One result per rigid body and comparison.
    # Keyed by (body, "before" or "after")
    bodies: dict[tuple[str, str], AlignmentResult]


def fit_alignment(
    optitrack: pd.DataFrame, gantry: pd.DataFrame, mask: BoolArray | None = None
) -> AlignmentTransform:
    """Find the rigid alignment that maps OptiTrack onto the gantry.

    ``optitrack`` and ``gantry`` have the columns time, x, y and z, and one row
    per sample. Only the samples selected by ``mask`` are used, or all of them
    if it is None.
    """
    if mask is not None:
        optitrack = optitrack[mask].reset_index(drop=True)
        gantry = gantry[mask].reset_index(drop=True)

    optitrack_time = optitrack["time"].to_numpy()
    optitrack_xyz = optitrack[XYZ].to_numpy()
    gantry_xyz = gantry[XYZ].to_numpy()

    def align(x: FloatArray) -> FloatArray:
        """OptiTrack positions aligned with the alignment vector ``x``."""
        alignment = AlignmentTransform.from_vector(x)
        return alignment.apply(optitrack_time, optitrack_xyz, ROT_CENTER)

    # Initial values of the parameters: no time shift, the known rotation about z,
    # and the translation that makes the mean positions coincide after rotating
    x0 = np.array([0.0, 0.0, 0.0, Z_ROT_GUESS, 0.0, 0.0, 0.0])
    x0[4:7] = np.nanmean(gantry_xyz - align(x0), axis=0)

    # Each rotation can move at most MAX_ROT from its initial value
    bounds = [(None, None)] * 7
    bounds[1] = (x0[1] - MAX_ROT, x0[1] + MAX_ROT)
    bounds[2] = (x0[2] - MAX_ROT, x0[2] + MAX_ROT)
    bounds[3] = (x0[3] - MAX_ROT, x0[3] + MAX_ROT)

    # Search for the parameters that minimize the mean squared distance between
    # the gantry positions and the aligned OptiTrack positions
    res = scp.optimize.minimize(
        fun=lambda x: samples_mse(gantry_xyz, align(x)),
        x0=x0,
        bounds=bounds,
        tol=1e-9,
        method="Powell",
        options={"disp": False},
    )

    if not res.success:
        logger.warning("The alignment fit did not converge: %s", res.message)

    return AlignmentTransform.from_vector(res.x)


def fit_alignment_without_tracking_errors(
    optitrack: pd.DataFrame, gantry: pd.DataFrame, valid: BoolArray
) -> AlignmentTransform:
    """Fit an alignment discarding the tracking errors of OptiTrack.

    The alignment is fitted twice. The first time it uses all the valid
    samples. The second time it excludes the samples that are at DROPOUT_MM
    or more from the gantry. These samples are considered tracking
    errors of the OptiTrack.

    Returns the second alignment.
    """
    first = fit_alignment(optitrack, gantry, mask=valid)
    residual = residual_3d(optitrack, gantry, first)
    keep = valid & (residual < DROPOUT_MM) & ~np.isnan(residual)
    return fit_alignment(optitrack, gantry, mask=keep)


def residual_vec(
    optitrack: pd.DataFrame, gantry: pd.DataFrame, alignment: AlignmentTransform
) -> FloatArray:
    """Aligned OptiTrack positions minus the gantry positions.

    Returns one row per sample, with the difference in x, y and z, in mm.
    """
    aligned = alignment.apply(
        optitrack["time"].to_numpy(), optitrack[XYZ].to_numpy(), ROT_CENTER
    )
    return aligned - gantry[XYZ].to_numpy()


def residual_3d(
    optitrack: pd.DataFrame, gantry: pd.DataFrame, alignment: AlignmentTransform
) -> FloatArray:
    """Distance between the aligned OptiTrack positions and the gantry ones.

    Returns one value per sample, in mm.
    """
    difference = residual_vec(optitrack, gantry, alignment)
    return np.sqrt(np.sum(difference**2, axis=1))


def stats(residual: FloatArray, mask: BoolArray) -> tuple[float, float, float, int]:
    """Statistics of the residual of the samples selected by ``mask``.

    Returns the root mean square, the median, the 95th percentile and the number
    of samples.
    """
    selected = residual[mask]
    selected = selected[~np.isnan(selected)]
    rmse = float(np.sqrt(np.mean(selected**2)))
    median = float(np.median(selected))
    p95 = float(np.percentile(selected, 95))
    return rmse, median, p95, len(selected)


def load_take(
    take: str, model: CorrectionModel, body: str = FRAME_BODY
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, BoolArray]:
    """Load the positions of a rigid body in a take.

    Returns:

    - The positions of the body measured by OptiTrack. They are in the OptiTrack
      coordinate system.
    - The positions of the body in the gantry coordinate system, before the
      correction.
    - The positions of the body in the gantry coordinate system, after
      correcting them with ``model``.
    - Bool array indicating the valid samples.

    The positions are dataframes with columns time, x, y and z. The time is
    seconds from the start of the OptiTrack capture. The x, y, z coordinates are
    in mm.

    The gantry records the position of the z-axis platform. The other bodies are
    mounted at a fixed offset from the z-axis platform, so their positions are
    obtained adding their offset to the z-axis platform position. The correction
    is applied to the z-axis platform position, and the offset is added afterwards.
    """
    optitrack_file = OPTITRACK_DIR / f"{take}_optitrack.csv"
    gantry_file = GROUND_TRUTH_DIR / f"{take}_ground_truth_gantry.csv"

    logger.info("[%s/%s] loading data...", take, body)

    # OptiTrack positions of the body, and the time at which the capture started
    optitrack_data, _ = load_optitrack_data(str(optitrack_file), rigid_body_name=body)
    metadata = load_optitrack_metadata(str(optitrack_file))
    capture_start = metadata["Capture Start Time"].timestamp()

    # Positions of the z-axis platform recorded by the gantry, and offset of the body
    # from the z-axis platform
    gantry_data = pd.read_csv(gantry_file)
    gantry_raw = gantry_data[[f"{FRAME_BODY}.{axis}" for axis in "XYZ"]].to_numpy()
    body_positions = gantry_data[[f"{body}.{axis}" for axis in "XYZ"]].to_numpy()
    offset = (body_positions - gantry_raw)[0]

    # The gantry and OptiTrack do not sample at the same instants.
    # Get the gantry positions at the instants of the OptiTrack samples.
    optitrack_time = optitrack_data["time"].to_numpy()
    gantry_time = gantry_data["time"].to_numpy() - capture_start
    gantry = interp_columns(optitrack_time, gantry_time, gantry_raw)

    # Gantry positions corrected with the model
    gantry_corrected = model.apply(gantry)

    def as_dataframe(positions: FloatArray) -> pd.DataFrame:
        df = pd.DataFrame(positions, columns=XYZ)
        df.insert(0, "time", optitrack_time)
        return df

    optitrack = as_dataframe(optitrack_data[["RB.X", "RB.Y", "RB.Z"]].to_numpy())
    gantry_before = as_dataframe(gantry + offset)
    gantry_after = as_dataframe(gantry_corrected + offset)

    # Samples that have both an OptiTrack position and a gantry position
    has_optitrack = ~optitrack[XYZ].isna().to_numpy().any(axis=1)
    has_gantry = ~gantry_after[XYZ].isna().to_numpy().any(axis=1)
    valid = has_optitrack & has_gantry

    return optitrack, gantry_before, gantry_after, valid


def apply_skip_initial(valid: BoolArray, optitrack: pd.DataFrame) -> BoolArray:
    """Mark as not valid the samples of the first SKIP_INITIAL_S seconds of a take.

    In that time the robot moves from rest to the start of its trajectory.
    """
    if SKIP_INITIAL_S > 0:
        t = optitrack["time"].to_numpy()
        valid = valid & ((t - t[0]) >= SKIP_INITIAL_S)
    return valid


def eval_alignment(
    optitrack: pd.DataFrame,
    gantry: pd.DataFrame,
    valid: BoolArray,
    take: str,
    label: str,
    alignment: AlignmentTransform,
) -> AlignmentResult:
    """Compare OptiTrack positions with gantry positions, given an alignment.

    The OptiTrack positions are aligned with ``alignment``, and then their
    distance to the gantry positions is computed for each sample. The samples
    that are not ``valid`` or are farther than DROPOUT_MM are left out of the
    statistics.

    ``take`` and ``label`` are only used in the log message.
    """
    # Distance between the aligned OptiTrack positions and the gantry ones
    residual = residual_3d(optitrack, gantry, alignment)

    # Samples to keep: the valid ones that are not tracking errors of OptiTrack
    keep = valid & (residual < DROPOUT_MM) & ~np.isnan(residual)

    rmse, median, p95, n = stats(residual, keep)
    n_drop = int(valid.sum() - keep.sum())
    residual_xyz = residual_vec(optitrack, gantry, alignment)[keep]

    logger.info(
        "[%s] %-6s: RMSE=%.2f  median=%.2f  P95=%.2f  (excl %d)",
        take,
        label,
        rmse,
        median,
        p95,
        n_drop,
    )

    return {
        "rmse": rmse,
        "median": median,
        "p95": p95,
        "n": n,
        "n_drop": n_drop,
        "alignment": alignment,
        "resid": residual[keep],
        "rvec": residual_xyz,
        "rmax": float(np.nanmax(residual[keep])),
        "r_all": residual,
        "valid": valid,
    }


def _fit_alignment_for_take(
    take: str, model: CorrectionModel, target: Target
) -> AlignmentTransform:
    """Fit the alignment of a take."""
    optitrack, gantry_before, gantry_after, valid = load_take(
        take, model, FRAME_BODY
    )
    gantry = gantry_after if target == "corrected" else gantry_before
    valid = apply_skip_initial(valid, optitrack)
    return fit_alignment_without_tracking_errors(optitrack, gantry, valid)


def fit_single_alignment(
    ref_take: str, model: CorrectionModel, target: Target
) -> AlignmentTransform:
    """Fit one alignment to use with all the takes.

    With ``ref_take`` set to "all", an alignment is fitted with each take and the
    result is the mean of their parameters. With the name of a take, the result is
    the alignment fitted with that take.

    ``target`` says which gantry positions OptiTrack is aligned with: the ones
    corrected with ``model`` or the uncorrected ones.
    """
    if ref_take in ("all", "mean"):
        logger.info(
            "Fitting the alignment on every take (%s gantry) and averaging...", target
        )
        take_alignments = []

        for take in TAKES:
            alignment = _fit_alignment_for_take(take, model, target).to_vector()
            take_alignments.append(alignment)
            logger.info("  [%s] %s", take, np.round(alignment, 4).tolist())

        alignments = np.array(take_alignments)
        mean_alignment = alignments.mean(axis=0)

        logger.info(
            "Mean alignment (%s) (dt, rx, ry, rz, tx, ty, tz) = %s",
            target,
            np.round(mean_alignment, 4).tolist(),
        )

        logger.info(
            "Std  across takes                              = %s",
            np.round(alignments.std(axis=0), 4).tolist(),
        )

        return AlignmentTransform.from_vector(mean_alignment)

    logger.info(
        "Fitting single alignment on reference take '%s' (%s gantry)...",
        ref_take,
        target,
    )

    alignment = _fit_alignment_for_take(ref_take, model, target)

    logger.info(
        "Single alignment (%s) (dt, rx, ry, rz, tx, ty, tz) = %s",
        target,
        np.round(alignment.to_vector(), 4).tolist(),
    )

    return alignment


def fit_take_alignments(
    take: str, model: CorrectionModel
) -> dict[str, AlignmentTransform]:
    """Fit the two alignments of a take.

    Returns the "before" alignment, fitted with the uncorrected gantry positions,
    and the "after" alignment, fitted with the gantry positions corrected with
    ``model``.
    """
    optitrack, gantry_before, gantry_after, valid = load_take(
        take, model, FRAME_BODY
    )
    valid = apply_skip_initial(valid, optitrack)

    alignments: dict[str, AlignmentTransform] = {}
    gantry_positions = {"before": gantry_before, "after": gantry_after}

    for label, gantry in gantry_positions.items():
        logger.info(
            "[%s] %-6s: fitting per-take alignment on %s...", take, label, FRAME_BODY
        )
        alignments[label] = fit_alignment_without_tracking_errors(
            optitrack, gantry, valid
        )

    return alignments


def process_take(
    take: str,
    model: CorrectionModel,
    bodies: list[str],
    alignments: Mapping[str, AlignmentTransform],
) -> TakeResult:
    """Compare the OptiTrack positions of the rigid bodies of a take with the gantry.

    Two comparisons are made for each body:

    - "before": with the gantry positions before the correction. The OptiTrack
      positions are aligned with ``alignments["before"]``.
    - "after": with the gantry positions corrected with ``model``. The OptiTrack
      positions are aligned with ``alignments["after"]``.

    This function does not fit the alignments. They are fitted before calling it,
    with ``fit_single_alignment`` or ``fit_take_alignments``. The same alignments
    are used with all the bodies.
    """
    t_start = time.perf_counter()
    out: TakeResult = {"take": take, "bodies": {}}

    for body in bodies:
        optitrack, gantry_before, gantry_after, valid = load_take(
            take, model, body
        )
        valid = apply_skip_initial(valid, optitrack)

        gantry_positions = {"before": gantry_before, "after": gantry_after}
        for label, gantry in gantry_positions.items():
            out["bodies"][(body, label)] = eval_alignment(
                optitrack, gantry, valid, take, f"{body}/{label}", alignments[label]
            )

    logger.info("[%s] done in %.1f s", take, time.perf_counter() - t_start)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATASET_DIR,
        help="dataset directory (must contain GROUND_TRUTH "
        "and OPTITRACK_MEASUREMENTS_CSV) (default: %(default)s)",
    )
    p.add_argument(
        "--calib",
        type=Path,
        default=CALIBRATION_FILE,
        help="calibration file with the parameters of the correction model "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--takes",
        nargs="+",
        default=TAKES,
        help="takes to process (default: the 7 dynamic ones)",
    )
    p.add_argument(
        "--bodies",
        nargs="+",
        default=BODIES,
        help=f"rigid bodies to compare with the gantry (default: {' '.join(BODIES)}). "
        f"The alignments are always fitted with {FRAME_BODY}",
    )
    p.add_argument(
        "--per-take-bodies",
        nargs="+",
        default=[FRAME_BODY],
        metavar="BODY",
        help="rigid bodies whose results are also printed for each take, or 'all' "
        f"for all of them (default: {FRAME_BODY})",
    )
    p.add_argument(
        "--dropout-mm",
        type=float,
        default=DROPOUT_MM,
        help="3D-residual threshold (mm) above which samples are "
        "considered as OptiTrack tracking glitches and are excluded "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--skip-initial-s",
        type=float,
        default=SKIP_INITIAL_S,
        help="exclude the first seconds of each take, (default: %(default)s)",
    )
    p.add_argument(
        "--per-take-alignment",
        action="store_true",
        help="fit the alignments with each take, instead of using a single alignment "
        "averaging all the takes.",
    )
    p.add_argument(
        "--ref-take",
        default="all",
        help="take to used for a single alignment, or 'all' to use an average of all "
        "the takes."
        "(default: %(default)s)",
    )
    p.add_argument(
        "--sensitivity-thresholds",
        type=float,
        nargs="*",
        default=None,
        metavar="MM",
        help="also print the result of the gantry positions after the correction for "
        "other values of --dropout-mm. Give the values in mm, or none to use a "
        "predefined list",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="do not print progress messages"
    )
    return p.parse_args()


def main() -> None:
    global DATASET_DIR, OPTITRACK_DIR, GROUND_TRUTH_DIR, CALIBRATION_FILE, TAKES
    global DROPOUT_MM, SKIP_INITIAL_S

    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    DATASET_DIR = args.dataset_dir
    OPTITRACK_DIR = DATASET_DIR / "OPTITRACK_MEASUREMENTS_CSV"
    GROUND_TRUTH_DIR = DATASET_DIR / "GROUND_TRUTH"
    CALIBRATION_FILE = args.calib
    TAKES = args.takes
    DROPOUT_MM = args.dropout_mm
    SKIP_INITIAL_S = args.skip_initial_s

    thresholds = None
    if args.sensitivity_thresholds is not None:
        thresholds = args.sensitivity_thresholds or SENS_THRESHOLDS

    model = load_correction(CALIBRATION_FILE)

    single = not args.per_take_alignment
    mode = (
        f"single alignment (ref take '{args.ref_take}'), one frame per comparison"
        if single
        else "per-take alignment (full 7 params)"
    )
    print(f"Alignment mode: {mode}")
    print(f"Glitch-rejection threshold --dropout-mm = {DROPOUT_MM:g} mm")
    print(f"Skip initial --skip-initial-s = {SKIP_INITIAL_S:g} s\n")

    single_alignments = None
    if single:
        single_alignments = {
            "before": fit_single_alignment(args.ref_take, model, "uncorrected"),
            "after": fit_single_alignment(args.ref_take, model, "corrected"),
        }

    # Compare OptiTrack with the gantry for all takes
    t_all = time.perf_counter()
    results: list[TakeResult] = []

    for i, take in enumerate(TAKES, 1):
        logger.info("=== take %d/%d: %s ===", i, len(TAKES), take)
        alignments = single_alignments or fit_take_alignments(take, model)
        results.append(process_take(take, model, args.bodies, alignments))

    logger.info(
        "all %d takes processed in %.1f s", len(TAKES), time.perf_counter() - t_all
    )

    def all_takes(
        body: str, label: str, key: Literal["resid", "rvec"] = "resid"
    ) -> FloatArray:
        """Residuals of a body in a comparison, with all the takes together."""
        return np.concatenate([res["bodies"][(body, label)][key] for res in results])

    # per-take detail for the selected bodies
    per_take_bodies = (
        args.bodies
        if "all" in args.per_take_bodies
        else [body for body in args.per_take_bodies if body in args.bodies]
    )
    for body in per_take_bodies:
        print(f"{body} per take:")
        print(
            f"{'take':10s} {'n':>6s}  "
            f"{'BEF rmse':>9s} {'med':>6s} {'p95':>6s}  "
            f"{'AFT rmse':>9s} {'med':>6s} {'p95':>6s}  {'excl':>6s}"
        )
        print("-" * 78)
        for res in results:
            before = res["bodies"][(body, "before")]
            after = res["bodies"][(body, "after")]
            print(
                f"{res['take']:10s} {after['n']:6d}  "
                f"{before['rmse']:9.2f} {before['median']:6.2f} {before['p95']:6.2f}  "
                f"{after['rmse']:9.2f} {after['median']:6.2f} {after['p95']:6.2f}  "
                f"{after['n_drop']:6d}"
            )
        print()

    # summary by rigid body, aggregated over all takes
    print("\nAggregated over all dynamic takes (mm):")
    print(
        f"{'body':10s} {'n':>6s}  "
        f"{'BEF rmse':>9s} {'med':>6s} {'p95':>6s}  "
        f"{'AFT rmse':>9s} {'med':>6s} {'p95':>6s}"
    )
    print("-" * 71)
    for body in args.bodies:
        before = all_takes(body, "before")
        after = all_takes(body, "after")
        print(
            f"{body:10s} {len(after):6d}  "
            f"{np.sqrt(np.mean(before**2)):9.2f} {np.median(before):6.2f} "
            f"{np.percentile(before, 95):6.2f}  "
            f"{np.sqrt(np.mean(after**2)):9.2f} {np.median(after):6.2f} "
            f"{np.percentile(after, 95):6.2f}"
        )

    # per-axis RMSE, all bodies, before and after
    print("\nPer-axis RMSE, aggregated over all dynamic takes (mm):")
    print(
        f"{'body':10s}  {'BEF X':>7s} {'BEF Y':>7s} {'BEF Z':>7s}  "
        f"{'AFT X':>7s} {'AFT Y':>7s} {'AFT Z':>7s}"
    )
    print("-" * 60)
    for body in args.bodies:
        rmse_before = np.sqrt(np.mean(all_takes(body, "before", "rvec") ** 2, axis=0))
        rmse_after = np.sqrt(np.mean(all_takes(body, "after", "rvec") ** 2, axis=0))
        print(
            f"{body:10s}  "
            + " ".join(f"{x:7.2f}" for x in rmse_before)
            + "  "
            + " ".join(f"{x:7.2f}" for x in rmse_after)
        )

    # Results for other values of the  threshold
    if thresholds:
        print(f"\nThreshold sensitivity ({FRAME_BODY} AFTER):")
        for threshold in thresholds:
            kept = []
            for res in results:
                after = res["bodies"][(FRAME_BODY, "after")]
                residual = after["r_all"]
                keep = after["valid"] & (residual < threshold) & ~np.isnan(residual)
                kept.append(residual[keep])
            residual = np.concatenate(kept)
            print(
                f"  thr={threshold:>10.0f}: n={len(residual):6d}  "
                f"RMSE={np.sqrt(np.mean(residual**2)):6.2f}  "
                f"median={np.median(residual):6.2f}  "
                f"P95={np.percentile(residual, 95):6.2f}"
            )


if __name__ == "__main__":
    main()
