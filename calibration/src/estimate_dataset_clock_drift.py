"""Estimate the clock drift between the gantry and OptiTrack in the RoboLoc-G dataset.

The time difference is modeled as an offset plus a drift. The gantry position at
time t is compared with the OptiTrack position at time

    t - (offset + drift * (t - t_ref))

where t is the absolute time and t_ref is the mean time of the campaign. The
offset is in seconds. The drift has no units and is printed in ppm.

The script does the following:

1. It fits one alignment for the whole campaign, as ``validate_dataset.py`` does,
   with the corrected gantry positions.
2. It searches for the offset and the drift that minimize the RMS distance
   between the OptiTrack and the gantry positions of all the takes together.

One offset and one drift are used for all the takes. With one offset per take,
the offsets would hide the drift. The clock drift makes the time difference change
from one take to the next. Using one offset requires that the capture start time
of each take is right.
"""

import argparse
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt
import scipy as scp
import validate_dataset as vd
from data import (
    AlignmentTransform,
    CorrectionModel,
    load_correction,
    load_optitrack_metadata,
)
from defaults import CALIBRATION_FILE, DATASET_DIR

logger = logging.getLogger("estimate_dataset_clock_drift")

# Limits of the search
MAX_OFFSET_MS = 200.0  # ms, largest offset
MAX_DRIFT_PPM = 300.0  # ppm, largest drift

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]


@dataclass
class Take:
    """Data of a take used to estimate the drift."""

    name: str
    capture_start: float  # s, absolute time of the start of the OptiTrack capture
    time: FloatArray  # s, time of each sample from the start of the capture
    optitrack: FloatArray  # mm, aligned OptiTrack positions, one x, y, z row per sample
    gantry: FloatArray  # mm, corrected gantry positions, one x, y, z row per sample

    # Samples used to compute the residual.
    # Set after loading all the takes with the value of samples_to_keep
    keep: BoolArray = field(init=False)

    @property
    def absolute_time(self) -> FloatArray:
        """Absolute time of each sample, in seconds."""
        return self.capture_start + self.time


def load_take(
    take: str, model: CorrectionModel, alignment: AlignmentTransform
) -> Take:
    """Load a take and align its OptiTrack positions with the gantry.

    The take is loaded as in ``validate_dataset.py``: the rigid body of the gantry,
    the gantry positions corrected with ``model``, and without the first seconds.
    """
    logger.info("[%s] loading...", take)
    optitrack_unaligned, _, gantry_corrected, valid = vd.load_take(
        take, model, vd.FRAME_BODY
    )
    valid = vd.apply_skip_initial(valid, optitrack_unaligned)

    optitrack = alignment.apply(
        optitrack_unaligned["time"].to_numpy(),
        optitrack_unaligned[vd.XYZ].to_numpy(),
        vd.ROT_CENTER,
    )
    gantry = gantry_corrected[vd.XYZ].to_numpy()

    # Remove the samples that are not valid or that have no position
    has_position = ~np.isnan(optitrack).any(axis=1) & ~np.isnan(gantry).any(axis=1)
    selected = valid & has_position
    time = optitrack_unaligned["time"].to_numpy()[selected]
    optitrack, gantry = optitrack[selected], gantry[selected]

    metadata = load_optitrack_metadata(str(vd.OPTITRACK_DIR / f"{take}_optitrack.csv"))

    return Take(
        name=take,
        capture_start=metadata["Capture Start Time"].timestamp(),
        time=time,
        optitrack=optitrack,
        gantry=gantry,
    )


def samples_to_keep(take: Take, t_ref: float) -> BoolArray:
    """Choose the samples of a take that are used to compute the residual.

    These samples are left out:

    - The tracking errors of OptiTrack (DROPOUT_MM or more from the gantry).
    - A margin at both ends of the take, because the samples of the ends are
      moved out of the take when the time is shifted. The margin is the largest
      time shift that the search can apply to a sample of the take.
    """
    max_time_to_ref = np.abs(take.absolute_time - t_ref).max()
    margin = MAX_OFFSET_MS * 1e-3 + MAX_DRIFT_PPM * 1e-6 * max_time_to_ref
    distance = np.linalg.norm(take.optitrack - take.gantry, axis=1)

    return (
        (distance < vd.DROPOUT_MM)
        & (take.time >= take.time[0] + margin)
        & (take.time <= take.time[-1] - margin)
    )


def shift_optitrack(
    take: Take, offset: float, drift_ppm: float, t_ref: float
) -> FloatArray:
    """OptiTrack positions of a take with its time shifted by an offset and a drift.

    The position of each sample is replaced by the OptiTrack position at the time
    of the sample minus ``offset + drift * (t - t_ref)``, where t is the absolute
    time of the sample. The positions are interpolated. They are NaN if that time
    is outside the take.
    """
    drift = drift_ppm * 1e-6
    shifted_time = take.time - (offset + drift * (take.absolute_time - t_ref))
    return np.column_stack(
        [
            np.interp(
                shifted_time,
                take.time,
                take.optitrack[:, axis],
                left=np.nan,
                right=np.nan,
            )
            for axis in range(3)
        ]
    )


def residuals(
    takes: list[Take], offset: float, drift_ppm: float, t_ref: float
) -> FloatArray:
    """Distance between OptiTrack and the gantry, for a given offset and drift.

    Returns one value per kept sample, in mm, with all the takes together.
    """
    distances = []
    for take in takes:
        difference = shift_optitrack(take, offset, drift_ppm, t_ref) - take.gantry
        distances.append(np.linalg.norm(difference, axis=1)[take.keep])
    return np.concatenate(distances)


def rms(takes: list[Take], offset: float, drift_ppm: float, t_ref: float) -> float:
    """Root mean square of the residuals, in mm."""
    return float(np.sqrt(np.mean(residuals(takes, offset, drift_ppm, t_ref) ** 2)))


def fit_offset(takes: list[Take], drift_ppm: float, t_ref: float) -> float:
    """Find the offset that minimizes the RMS, for a given drift.

    Returns the offset in seconds.
    """
    res = scp.optimize.minimize_scalar(
        lambda offset: rms(takes, offset, drift_ppm, t_ref),
        bounds=(-MAX_OFFSET_MS * 1e-3, MAX_OFFSET_MS * 1e-3),
        method="bounded",
    )

    if not res.success:
        logger.warning("The offset fit did not converge: %s", res.message)

    return float(res.x)


def fit_offset_and_drift(takes: list[Take], t_ref: float) -> tuple[float, float, float]:
    """Find the offset and the drift that minimize the RMS.

    Returns the offset in seconds, the drift in ppm and the RMS in mm.
    """
    res = scp.optimize.minimize(
        lambda x: rms(takes, x[0], x[1], t_ref),
        x0=np.zeros(2),
        method="Powell",
        tol=1e-12,
        bounds=[
            (-MAX_OFFSET_MS * 1e-3, MAX_OFFSET_MS * 1e-3),
            (-MAX_DRIFT_PPM, MAX_DRIFT_PPM),
        ],
    )

    if not res.success:
        logger.warning("The offset and drift fit did not converge: %s", res.message)

    return float(res.x[0]), float(res.x[1]), float(res.fun)


def print_takes(takes: list[Take], span: float) -> None:
    """Print the start, the duration and the number of samples of each take."""
    campaign_start = min(take.absolute_time[0] for take in takes)
    num_samples = sum(len(take.time) for take in takes)
    print(
        f"\n{len(takes)} takes, {num_samples} paired samples, "
        f"campaign span {span:.0f} s"
    )
    for take in takes:
        start = take.absolute_time[0] - campaign_start
        duration = take.time[-1] - take.time[0]
        print(
            f"  {take.name:10s} start +{start:7.1f} s  "
            f"duration {duration:6.1f} s  {len(take.time):6d} samples"
        )


def print_scan(
    takes: list[Take], t_ref: float, scan: list[float], span: float
) -> None:
    """Print the RMS for several values of the drift.

    ``scan`` gives the first value, the last value and the step, in ppm. The offset
    is fitted again for each value of the drift. The last column is the time
    difference that the drift adds over the whole campaign.
    """
    first, last, step = scan
    print("\ndrift scan (single offset, refitted at each point)")
    print(
        f"  {'drift_ppm':>9s} {'RMS3D_mm':>9s} {'offset_ms':>10s} "
        f"{'accumulated_ms':>15s}"
    )
    for drift_ppm in np.arange(first, last + step / 2, step):
        offset = fit_offset(takes, drift_ppm, t_ref)
        print(
            f"  {drift_ppm:+9.1f} {rms(takes, offset, drift_ppm, t_ref):9.3f} "
            f"{offset * 1e3:10.2f} {drift_ppm * 1e-6 * span * 1e3:+15.1f}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
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
        default=vd.TAKES,
        help="takes to use (default: the 7 dynamic ones)",
    )
    p.add_argument(
        "--scan",
        type=float,
        nargs=3,
        metavar=("FROM", "TO", "STEP"),
        default=[-60.0, 60.0, 10.0],
        help="values of the drift, in ppm, for which the RMS is printed "
        "(default: %(default)s)",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="do not print progress messages"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Override validate_dataset.py settings
    vd.DATASET_DIR = args.dataset_dir
    vd.OPTITRACK_DIR = vd.DATASET_DIR / "OPTITRACK_MEASUREMENTS_CSV"
    vd.GROUND_TRUTH_DIR = vd.DATASET_DIR / "GROUND_TRUTH"
    vd.TAKES = args.takes

    model = load_correction(args.calib)

    # One alignment for the whole campaign: the mean of the alignments of the takes
    alignment = vd.fit_single_alignment("all", model, "corrected")

    takes = [load_take(take, model, alignment) for take in args.takes]

    # Mean time of the campaign, and time from its first sample to its last one
    t_ref = float(np.mean([take.absolute_time.mean() for take in takes]))
    span = max(take.absolute_time[-1] for take in takes) - min(
        take.absolute_time[0] for take in takes
    )

    for take in takes:
        take.keep = samples_to_keep(take, t_ref)

    print_takes(takes, span)
    print_scan(takes, t_ref, args.scan, span)

    # Offset and drift fitted together
    offset, drift_ppm, rms_fit = fit_offset_and_drift(takes, t_ref)
    print("\njoint fit (single offset and drift, absolute time base)")
    print(
        f"  offset {offset * 1e3:+.2f} ms, drift {drift_ppm:+.2f} ppm, "
        f"RMS {rms_fit:.3f} mm"
    )
    print(f"  {drift_ppm * 1e-6 * span * 1e3:+.1f} ms accumulated over the campaign")

    # Only the offset fitted, with no drift
    rms_no_drift = rms(takes, fit_offset(takes, 0.0, t_ref), 0.0, t_ref)
    print(
        f"\nRMS with no drift, single offset: {rms_no_drift:.3f} mm "
        f"({rms_no_drift - rms_fit:+.3f} mm over the global fit)"
    )


if __name__ == "__main__":
    main()
