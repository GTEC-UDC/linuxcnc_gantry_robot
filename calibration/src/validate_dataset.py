#!/usr/bin/env python3
"""
Out-of-sample validation of the gantry kinematic correction on the RoboLoc-G
(July 2025) campaign.

The correction parameters fitted on the calibration capture are
applied to the July gantry trajectories, and the result is compared against the
OptiTrack "Grua" rigid body. Two figures are reported:

    BEFORE : residual between OptiTrack and the UNCORRECTED gantry
    AFTER  : residual between OptiTrack and the CORRECTED gantry

Each comparison is aligned against its OWN target. This matters: the correction
displaces the gantry by mean(correct(p) - p), which is ~0 over the calibration
workspace (least squares balances c against the other terms of the model) but
~2.3 mm over the July trajectories. Reusing the uncorrected frame for the AFTER
residual would inject that offset as a bias and understate the correction.

Note the correction acts on the GANTRY coordinates, which are already in the
gantry frame, so applying it needs no alignment; the alignment is what brings
OptiTrack into that frame. They act on different data.

By default a SINGLE alignment is used per comparison, averaged over all takes
(the convention of the published dataset, and the one comparable to the
in-sample calibration figure). --per-take-alignment fits one alignment per take
instead, which additionally removes the take-to-take frame variation and is
useful as a diagnostic.

Read-only: it does not modify the dataset, the pipeline, or the paper.

Run (from this directory, using the local venv):
    .venv/bin/python validate_dataset.py [options]
    .venv/bin/python validate_dataset.py --help
"""

import argparse
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy as scp
from coordinates_utils import coord_mse
from data import (
    coord_align,
    coord_calibrate,
    interp_columns,
    load_correction_params,
    load_optitrack_data,
    load_optitrack_metadata,
)
from defaults import CALIBRATION_FILE, DATASET_DIR

logger = logging.getLogger("validate_dataset")

OPTITRACK_DIR = DATASET_DIR / "OPTITRACK_MEASUREMENTS_CSV"
GROUND_TRUTH_DIR = DATASET_DIR / "GROUND_TRUTH"

# Internal parameters of the alignment fit (not exposed: never needed tuning)
ROT_CENTER = (0.0, 0.0, 1500.0)
Z_ROT_GUESS = -1.6520  # rad, ~ -94.66 deg, initial guess for the fit
MAX_ROT = 0.15  # rad, bound around the init for each rotation

# Defaults (overridable from the command line, see parse_args)
TAKES = ["circle", "random1", "random2", "zigzag1", "zigzag2", "zigzag3", "zigzag4"]
BODIES = ["Grua", "UWB_tag", "FTM_tag", "Feet"]
FRAME_BODY = "Grua"  # the frame is always estimated from the platform
DROPOUT_MM = 15.0  # mm, 3D-residual glitch-rejection threshold
SKIP_INITIAL_S = 6.0  # s, drop the approach transient at the take start
SENS_THRESHOLDS = [1e9, 200, 100, 50, 30, 20, 15]  # mm, sensitivity sweep (after)


def fit_alignment(df_rb, df_target, mask=None):
    """Fit the 7-param rigid alignment mapping df_rb (opti) onto df_target (gantry)."""
    rb = df_rb if mask is None else df_rb[mask].reset_index(drop=True)
    tg = df_target if mask is None else df_target[mask].reset_index(drop=True)

    # analytic translation init given the z-rotation guess
    x0 = np.array([0.0, 0.0, 0.0, Z_ROT_GUESS, 0.0, 0.0, 0.0])
    rot0 = coord_align(x0, rb, ROT_CENTER)
    d = tg[["x", "y", "z"]].to_numpy() - rot0[["x", "y", "z"]].to_numpy()
    x0[4:7] = np.nanmean(d, axis=0)

    bounds = [(None, None)] * 7
    bounds[1] = (x0[1] - MAX_ROT, x0[1] + MAX_ROT)
    bounds[2] = (x0[2] - MAX_ROT, x0[2] + MAX_ROT)
    bounds[3] = (x0[3] - MAX_ROT, x0[3] + MAX_ROT)

    res = scp.optimize.minimize(
        fun=lambda x: coord_mse(tg, coord_align(x, rb, ROT_CENTER)),
        x0=x0,
        bounds=bounds,
        tol=1e-9,
        method="Powell",
        options={"disp": False},
    )
    return res.x


def residual_vec(df_rb, df_target, params):
    aligned = coord_align(params, df_rb, ROT_CENTER)
    return aligned[["x", "y", "z"]].to_numpy() - df_target[["x", "y", "z"]].to_numpy()


def residual_3d(df_rb, df_target, params):
    return np.sqrt(np.sum(residual_vec(df_rb, df_target, params) ** 2, axis=1))


def stats(res, mask):
    r = res[mask]
    r = r[~np.isnan(r)]
    rmse = float(np.sqrt(np.mean(r**2)))
    return rmse, float(np.median(r)), float(np.percentile(r, 95)), len(r)


def load_take(take, corr_params, body=FRAME_BODY):
    """Load one rigid body of a take and build its (un)corrected references.

    The reference for a mobile body is the gantry platform plus its fixed offset
    (the dataset's eq:mobile-position). The correction is applied to the
    PLATFORM and the offset added afterwards, because correct() is nonlinear and
    correct(p + o) != correct(p) + o.

    Returns (df_rb, tgt_before, tgt_after, valid), the OptiTrack track of `body`
    and its uncorrected/corrected references, in gantry coordinates and
    time-indexed to the OptiTrack samples.
    """
    opti_csv = OPTITRACK_DIR / f"{take}_optitrack.csv"
    gt_csv = GROUND_TRUTH_DIR / f"{take}_ground_truth_gantry.csv"

    logger.info("[%s/%s] loading data...", take, body)
    df_o, _ = load_optitrack_data(str(opti_csv), rigid_body_name=body)
    meta = load_optitrack_metadata(str(opti_csv))
    t0 = meta["Capture Start Time"].timestamp()

    gt = pd.read_csv(gt_csv)
    plat = gt[[f"{FRAME_BODY}.{a}" for a in "XYZ"]].to_numpy()
    offset = (gt[[f"{body}.{a}" for a in "XYZ"]].to_numpy() - plat)[0]

    t_o = df_o["time"].to_numpy()
    gan = interp_columns(t_o, gt["time"].to_numpy() - t0, plat)

    # corrected platform (fixed params); no alignment involved
    gcal = coord_calibrate(corr_params, pd.DataFrame(gan, columns=["x", "y", "z"]))[
        ["x", "y", "z"]
    ].to_numpy()

    def as_df(arr):
        out = pd.DataFrame(arr, columns=["x", "y", "z"])
        out.insert(0, "time", t_o)
        return out

    df_rb = as_df(df_o[["RB.X", "RB.Y", "RB.Z"]].to_numpy())
    tgt_before = as_df(gan + offset)
    tgt_after = as_df(gcal + offset)

    # valid = rows where both the OptiTrack and the gantry are present
    valid = ~df_rb[["x", "y", "z"]].isna().to_numpy().any(axis=1) & ~tgt_after[
        ["x", "y", "z"]
    ].isna().to_numpy().any(axis=1)

    return df_rb, tgt_before, tgt_after, valid


def apply_skip_initial(valid, df_rb):
    """Exclude the first SKIP_INITIAL_S seconds of the take (the approach move)."""
    if SKIP_INITIAL_S > 0:
        t = df_rb["time"].to_numpy()
        valid = valid & ((t - t[0]) >= SKIP_INITIAL_S)
    return valid


def eval_alignment(df_rb, tgt, valid, take, label, params):
    """Apply the given alignment to the OptiTrack track and return the stats."""
    p = np.asarray(params)
    r = residual_3d(df_rb, tgt, p)
    clean = valid & (r < DROPOUT_MM) & ~np.isnan(r)

    rmse, med, p95, n = stats(r, clean)
    n_drop = int(valid.sum() - clean.sum())
    rvec = residual_vec(df_rb, tgt, p)[clean]

    logger.info(
        "[%s] %-6s: RMSE=%.2f  median=%.2f  P95=%.2f  (excl %d)",
        take,
        label,
        rmse,
        med,
        p95,
        n_drop,
    )

    return {
        "rmse": rmse,
        "median": med,
        "p95": p95,
        "n": n,
        "n_drop": n_drop,
        "params": np.asarray(p).tolist(),
        "resid": r[clean],
        "rvec": rvec,
        "rmax": float(np.nanmax(r[clean])),
        "r_all": r,
        "valid": valid,
    }


def _fit_alignment_for_take(take, corr_params, target):
    """Per-take alignment against the chosen gantry target, with glitch rejection."""
    df_rb, tgt_before, tgt_after, valid = load_take(take, corr_params, FRAME_BODY)
    tgt = tgt_after if target == "corrected" else tgt_before
    valid = apply_skip_initial(valid, df_rb)
    p = fit_alignment(df_rb, tgt, mask=valid)
    r = residual_3d(df_rb, tgt, p)
    clean = valid & (r < DROPOUT_MM) & ~np.isnan(r)
    return fit_alignment(df_rb, tgt, mask=clean)


def fit_single_alignment(ref_take, corr_params, target):
    """Fit ONE campaign-wide alignment against the given gantry target.

    With ref_take='all' every take is fitted and the parameters averaged, which
    avoids depending on a single (possibly atypical) take.
    """
    if ref_take in ("all", "mean"):
        logger.info(
            "Fitting the alignment on every take (%s gantry) and averaging...", target
        )
        params = []
        for take in TAKES:
            p = _fit_alignment_for_take(take, corr_params, target)
            params.append(p)
            logger.info("  [%s] %s", take, np.round(p, 4).tolist())
        arr = np.array(params)
        p = arr.mean(axis=0)
        logger.info(
            "Mean alignment (%s) (dt, rx, ry, rz, tx, ty, tz) = %s",
            target,
            np.round(p, 4).tolist(),
        )
        logger.info(
            "Std  across takes                              = %s",
            np.round(arr.std(axis=0), 4).tolist(),
        )
        return p

    logger.info(
        "Fitting single alignment on reference take '%s' (%s gantry)...",
        ref_take,
        target,
    )
    p = _fit_alignment_for_take(ref_take, corr_params, target)
    logger.info(
        "Single alignment (%s) (dt, rx, ry, rz, tx, ty, tz) = %s",
        target,
        np.round(p, 4).tolist(),
    )
    return p


def fit_take_frames(take, corr_params):
    """Per-take frames, fitted on the platform, one per target."""
    df_rb, tgt_before, tgt_after, valid = load_take(take, corr_params, FRAME_BODY)
    valid = apply_skip_initial(valid, df_rb)
    frames = {}
    for label, tgt in [("before", tgt_before), ("after", tgt_after)]:
        logger.info(
            "[%s] %-6s: fitting per-take frame on %s...", take, label, FRAME_BODY
        )
        p = fit_alignment(df_rb, tgt, mask=valid)
        r = residual_3d(df_rb, tgt, p)
        clean = valid & (r < DROPOUT_MM) & ~np.isnan(r)
        frames[label] = fit_alignment(df_rb, tgt, mask=clean)
    return frames


def process_take(take, corr_params, bodies, frames):
    """Evaluate every rigid body of a take with the given frames.

    frames is {"before": params, "after": params}; the same frame is applied to
    all bodies, as the dataset does (there is one physical frame relationship).
    """
    t_start = time.perf_counter()
    out = {"take": take, "bodies": {}}
    for body in bodies:
        df_rb, tgt_before, tgt_after, valid = load_take(take, corr_params, body)
        valid = apply_skip_initial(valid, df_rb)
        for label, tgt in [("before", tgt_before), ("after", tgt_after)]:
            out["bodies"][(body, label)] = eval_alignment(
                df_rb, tgt, valid, take, f"{body}/{label}", frames[label]
            )
    logger.info("[%s] done in %.1f s", take, time.perf_counter() - t_start)
    return out


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATASET_DIR,
        help="dataset directory (must contain GANTRY_MEASUREMENTS "
        "and OPTITRACK_MEASUREMENTS_CSV) (default: %(default)s)",
    )
    p.add_argument(
        "--calib",
        type=Path,
        default=CALIBRATION_FILE,
        help="JSON file with the fixed correction parameters (default: %(default)s)",
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
        help=f"rigid bodies to evaluate (default: {' '.join(BODIES)}); "
        f"the frame is always estimated from {FRAME_BODY}",
    )
    p.add_argument(
        "--per-take-bodies",
        nargs="+",
        default=[FRAME_BODY],
        metavar="BODY",
        help=f"bodies to break down per take; 'all' for every "
        f"evaluated body (default: {FRAME_BODY})",
    )
    p.add_argument(
        "--dropout-mm",
        type=float,
        default=DROPOUT_MM,
        help="3D-residual threshold (mm) above which a sample is "
        "treated as an OptiTrack tracking glitch and excluded "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--skip-initial-s",
        type=float,
        default=SKIP_INITIAL_S,
        help="exclude the first N seconds of each take, covering the "
        "robot's approach move from rest (default: %(default)s)",
    )
    p.add_argument(
        "--per-take-alignment",
        action="store_true",
        help="fit one alignment per take instead of a single "
        "campaign-wide one; also removes the take-to-take frame "
        "variation, so it is a diagnostic rather than the "
        "headline figure",
    )
    p.add_argument(
        "--ref-take",
        default="all",
        help="take providing the single alignment; 'all' fits every "
        "take and averages the parameters (default: %(default)s)",
    )
    p.add_argument(
        "--sensitivity-thresholds",
        type=float,
        nargs="*",
        default=None,
        metavar="MM",
        help="also print how the global AFTER residual varies with the "
        "glitch threshold; pass the thresholds in mm, or the flag "
        "alone to use the built-in list. Off by default",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="suppress per-take progress logging"
    )
    return p.parse_args()


def main():
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

    sens = (
        None
        if args.sensitivity_thresholds is None
        else (args.sensitivity_thresholds or SENS_THRESHOLDS)
    )

    corr_params = load_correction_params(CALIBRATION_FILE)

    single = not args.per_take_alignment
    mode = (
        f"single alignment (ref take '{args.ref_take}'), one frame per comparison"
        if single
        else "per-take alignment (full 7 params)"
    )
    print(f"Alignment mode: {mode}")
    print(f"Glitch-rejection threshold --dropout-mm = {DROPOUT_MM:g} mm")
    print(f"Skip initial --skip-initial-s = {SKIP_INITIAL_S:g} s\n")

    # Each comparison is aligned against its own target: the BEFORE residual
    # against the uncorrected gantry, the AFTER one against the corrected gantry.
    fixed_frames = None
    if single:
        fixed_frames = {
            "before": fit_single_alignment(args.ref_take, corr_params, "uncorrected"),
            "after": fit_single_alignment(args.ref_take, corr_params, "corrected"),
        }

    t_all = time.perf_counter()
    results = []
    for i, take in enumerate(TAKES, 1):
        logger.info("=== take %d/%d: %s ===", i, len(TAKES), take)
        frames = fixed_frames or fit_take_frames(take, corr_params)
        results.append(process_take(take, corr_params, args.bodies, frames))
    logger.info(
        "all %d takes processed in %.1f s", len(TAKES), time.perf_counter() - t_all
    )

    def pool(body, label, key="resid"):
        return np.concatenate([o["bodies"][(body, label)][key] for o in results])

    # per-take detail for the selected bodies
    pt_bodies = (
        args.bodies
        if "all" in args.per_take_bodies
        else [b for b in args.per_take_bodies if b in args.bodies]
    )
    for body in pt_bodies:
        print(f"{body} per take:")
        print(
            f"{'take':10s} {'n':>6s}  "
            f"{'BEF rmse':>9s} {'med':>6s} {'p95':>6s}  "
            f"{'AFT rmse':>9s} {'med':>6s} {'p95':>6s}  {'excl':>6s}"
        )
        print("-" * 78)
        for o in results:
            b = o["bodies"][(body, "before")]
            a = o["bodies"][(body, "after")]
            print(
                f"{o['take']:10s} {a['n']:6d}  "
                f"{b['rmse']:9.2f} {b['median']:6.2f} {b['p95']:6.2f}  "
                f"{a['rmse']:9.2f} {a['median']:6.2f} {a['p95']:6.2f}  {a['n_drop']:6d}"
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
        cells = []
        for label in ["before", "after"]:
            r = pool(body, label)
            cells.append(
                (np.sqrt(np.mean(r**2)), np.median(r), np.percentile(r, 95), len(r))
            )
        (br, bm, bp, _), (ar, am, ap, an) = cells
        print(
            f"{body:10s} {an:6d}  {br:9.2f} {bm:6.2f} {bp:6.2f}  "
            f"{ar:9.2f} {am:6.2f} {ap:6.2f}"
        )

    # per-axis RMSE, all bodies, before and after
    print("\nPer-axis RMSE, aggregated over all dynamic takes (mm):")
    print(
        f"{'body':10s}  {'BEF X':>7s} {'BEF Y':>7s} {'BEF Z':>7s}  "
        f"{'AFT X':>7s} {'AFT Y':>7s} {'AFT Z':>7s}"
    )
    print("-" * 60)
    for body in args.bodies:
        vals = []
        for label in ["before", "after"]:
            v = pool(body, label, "rvec")
            vals += [np.sqrt(np.mean(v[:, i] ** 2)) for i in range(3)]
        print(
            f"{body:10s}  "
            + " ".join(f"{x:7.2f}" for x in vals[:3])
            + "  "
            + " ".join(f"{x:7.2f}" for x in vals[3:])
        )

    # dropout-threshold sensitivity on the platform after residual (opt-in)
    if sens:
        print(f"\nThreshold sensitivity ({FRAME_BODY} AFTER):")
        for thr in sens:
            rs = []
            for o in results:
                d = o["bodies"][(FRAME_BODY, "after")]
                r = d["r_all"]
                rs.append(r[d["valid"] & (r < thr) & ~np.isnan(r)])
            r = np.concatenate(rs)
            print(
                f"  thr={thr:>10.0f}: n={len(r):6d}  "
                f"RMSE={np.sqrt(np.mean(r**2)):6.2f}  "
                f"median={np.median(r):6.2f}  P95={np.percentile(r, 95):6.2f}"
            )


if __name__ == "__main__":
    main()
