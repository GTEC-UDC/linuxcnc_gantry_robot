"""Residual clock drift between the gantry and OptiTrack over the RoboLoc-G campaign.

``estimate_clock_drift.py`` fits the drift from the velocity profiles of a single
capture. That works on the 22-minute calibration capture, but not on this dataset:
its takes last 45 to 160 s and several of them are periodic (the zigzags), so the
time offset is aliased and the unbounded search in ``fit_drift`` settles on a shift
of a whole motion period. This script fits every take at once instead, on positions.

The time model is the one of ``estimate_clock_drift.time_shifted``: the OptiTrack
clock reads t while the true instant is t - (dt + drift * (t - t_ref)). A single
offset and a single drift are fitted for the whole campaign, on absolute time, so
the 34 minutes spanned by the takes act as the lever arm rather than the duration of
any one of them.

Sharing the offset is what makes the fit sensitive. Giving each take its own offset
would absorb the ramp a campaign-wide rate difference produces and leave only the
curvature inside a take, which 39 to 154 s cannot resolve. Sharing it also relies on
the absolute capture start time of each take being right, which the result confirms:
a wrong start time would show up as a residual well above the published one.

The frame alignment is fitted once, up front, by ``validate_dataset.py`` and its
averaged parameters are then held fixed, so neither the frame nor the correction
model can absorb any of the drift. The offsets fitted here are residuals on top of
the time shift that alignment already applies.

Read-only: it does not modify the dataset, the pipeline, or the paper.

Run (from this directory, using the local venv):
    .venv/bin/python estimate_dataset_drift.py [options]
    .venv/bin/python estimate_dataset_drift.py --help
"""

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy as scp
import validate_dataset as vd
from data import coord_align, load_optitrack_metadata

logger = logging.getLogger("estimate_dataset_drift")

SRC = Path(__file__).resolve().parent
DATASET_DIR = SRC.parents[2] / "roboloc-g-dataset-code/data/roboloc-g"
CALIBRATION_FILE = (
    SRC.parents[1] / "calibration/measurements/2025-04-09/calibration.json"
)

BOUND_MS = 200.0  # bound of the offset search, wide enough for any residual offset
BOUND_PPM = 300.0  # bound of the drift search


@dataclass
class Take:
    """One take, reduced to the arrays the objective needs on every evaluation.

    ``mask`` fixes the samples the residual is computed on, and is decided once,
    before the search. Rejecting glitches inside the objective would let the fit
    lower the residual by warping the time base until the samples that no longer
    agree cross the rejection threshold and are dropped, which discards data rather
    than improving the alignment. It also trims the ends of the take, so no sample
    can fall outside the interpolation range for any warp within the search bounds.
    """

    name: str
    t_rel: np.ndarray  # OptiTrack sample times, relative to the capture start
    t0: float  # absolute time of the capture start
    opti: np.ndarray  # OptiTrack platform positions, in the gantry frame (n, 3)
    gantry: np.ndarray  # corrected gantry positions at t_rel (n, 3)
    mask: np.ndarray  # samples the residual is evaluated on (n,)

    @property
    def t_abs(self) -> np.ndarray:
        """Sample times on the absolute campaign clock, which the drift refers to."""
        return self.t0 + self.t_rel


def load_take(name, corr_params, frame):
    """Load one take and bring its OptiTrack track into the gantry frame.

    Reuses ``validate_dataset.load_take``, so the correction parameters, the
    ground-truth reference and the initial-transient rejection are exactly the ones
    behind the published figures.
    """
    logger.info("[%s] loading...", name)
    df_rb, _, target, valid = vd.load_take(name, corr_params, vd.FRAME_BODY)
    valid = vd.apply_skip_initial(valid, df_rb)

    aligned = coord_align(frame, df_rb, vd.ROT_CENTER)
    opti = aligned[["x", "y", "z"]].to_numpy()
    gantry = target[["x", "y", "z"]].to_numpy()

    keep = valid & ~np.isnan(opti).any(axis=1) & ~np.isnan(gantry).any(axis=1)
    t_rel = df_rb["time"].to_numpy()[keep]
    opti, gantry = opti[keep], gantry[keep]

    # Fixed evaluation set: the glitch rejection of validate_dataset.py, applied once
    # at the nominal hypothesis, and a margin at both ends covering the largest warp
    # the search can reach.
    margin = BOUND_MS * 1e-3 + BOUND_PPM * 1e-6 * (t_rel[-1] - t_rel[0])
    mask = (
        (np.linalg.norm(opti - gantry, axis=1) < vd.DROPOUT_MM)
        & (t_rel >= t_rel[0] + margin)
        & (t_rel <= t_rel[-1] - margin)
    )

    meta = load_optitrack_metadata(str(vd.OPTITRACK_DIR / f"{name}_optitrack.csv"))

    return Take(
        name=name,
        t_rel=t_rel,
        t0=meta["Capture Start Time"].timestamp(),
        opti=opti,
        gantry=gantry,
        mask=mask,
    )


def warp(take, dt, drift, t_ref):
    """OptiTrack positions of a take with its time base warped by (dt, drift).

    Mirrors ``estimate_clock_drift.time_shifted``: a positive dt means the OptiTrack
    clock runs ahead of the gantry one. The drift is referred to absolute time, so a
    single value describes the whole campaign.
    """
    shifted = take.t_rel - (dt + drift * (take.t_abs - t_ref))
    return np.column_stack(
        [
            np.interp(shifted, take.t_rel, take.opti[:, k], left=np.nan, right=np.nan)
            for k in range(3)
        ]
    )


def residuals(takes, dts, drift, t_ref):
    """3D residual over the fixed evaluation set of each take."""
    out = []
    for take, dt in zip(takes, dts):
        err = warp(take, dt, drift, t_ref) - take.gantry
        out.append(np.linalg.norm(err, axis=1)[take.mask])
    return np.concatenate(out)


def rms(takes, dts, drift, t_ref):
    return float(np.sqrt(np.mean(residuals(takes, dts, drift, t_ref) ** 2)))


def fit_offset(takes, t_ref, drift_ppm):
    """Best single offset shared by every take, at a fixed drift."""
    res = scp.optimize.minimize_scalar(
        lambda dt: rms(takes, [dt] * len(takes), drift_ppm * 1e-6, t_ref),
        bounds=(-BOUND_MS * 1e-3, BOUND_MS * 1e-3),
        method="bounded",
    )
    return float(res.x)


def fit_global(takes, t_ref):
    """One offset and one drift for the whole campaign, on absolute time."""
    res = scp.optimize.minimize(
        lambda x: rms(takes, [x[0]] * len(takes), x[1] * 1e-6, t_ref),
        x0=np.zeros(2),
        method="Powell",
        tol=1e-12,
        bounds=[(-BOUND_MS * 1e-3, BOUND_MS * 1e-3), (-BOUND_PPM, BOUND_PPM)],
    )
    return float(res.x[0]), float(res.x[1]), float(res.fun)


def print_takes(takes):
    span = max(t.t_abs[-1] for t in takes) - min(t.t_abs[0] for t in takes)
    first = min(t.t_abs[0] for t in takes)
    n = sum(len(t.t_rel) for t in takes)
    print(f"\n{len(takes)} takes, {n} paired samples, campaign span {span:.0f} s")
    for t in takes:
        print(
            f"  {t.name:10s} start +{t.t_abs[0] - first:7.1f} s  "
            f"duration {t.t_rel[-1] - t.t_rel[0]:6.1f} s  {len(t.t_rel):6d} samples"
        )
    return span


def print_scan(takes, t_ref, scan, span):
    """Residual against imposed drift, with the shared offset refitted at each point.

    Refitting the offset at every point keeps the scan from crediting a drift with
    what a constant offset already explains, so the curve shows what the rate
    difference alone costs.
    """
    lo, hi, step = scan
    print("\ndrift scan (single offset, refitted at each point)")
    print(
        f"  {'drift_ppm':>9s} {'RMS3D_mm':>9s} {'offset_ms':>10s} "
        f"{'accumulated_ms':>15s}"
    )
    for d in np.arange(lo, hi + step / 2, step):
        dt = fit_offset(takes, t_ref, d)
        print(
            f"  {d:+9.1f} {rms(takes, [dt] * len(takes), d * 1e-6, t_ref):9.3f} "
            f"{dt * 1e3:10.2f} {d * 1e-6 * span * 1e3:+15.1f}"
        )


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATASET_DIR,
        help="dataset directory (default: %(default)s)",
    )
    p.add_argument(
        "--calib",
        type=Path,
        default=CALIBRATION_FILE,
        help="JSON file with the fixed correction parameters",
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
        help="drift scan in ppm, offsets refitted at each point",
    )
    p.add_argument("-q", "--quiet", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    vd.DATASET_DIR = args.dataset_dir
    vd.OPTITRACK_DIR = vd.DATASET_DIR / "OPTITRACK_MEASUREMENTS_CSV"
    vd.GROUND_TRUTH_DIR = vd.DATASET_DIR / "GROUND_TRUTH"
    vd.TAKES = args.takes

    with open(args.calib) as f:
        corr_params = np.array(json.load(f)["correction"])

    # One frame for the whole campaign, averaged over the takes and held fixed
    frame = vd.fit_single_alignment("all", corr_params, "corrected")

    takes = [load_take(n, corr_params, frame) for n in args.takes]
    t_ref = float(np.mean([t.t_abs.mean() for t in takes]))

    span = print_takes(takes)
    print_scan(takes, t_ref, args.scan, span)

    dt_g, drift_g, rms_g = fit_global(takes, t_ref)
    print("\njoint fit (single offset and drift, absolute time base)")
    print(
        f"  offset {dt_g * 1e3:+.2f} ms, drift {drift_g:+.2f} ppm, RMS {rms_g:.3f} mm"
    )
    print(f"  {drift_g * 1e-6 * span * 1e3:+.1f} ms accumulated over the campaign")

    ref = rms(takes, [fit_offset(takes, t_ref, 0.0)] * len(takes), 0.0, t_ref)
    print(
        f"\nRMS with no drift, single offset: {ref:.3f} mm "
        f"({ref - rms_g:+.3f} mm over the global fit)"
    )


if __name__ == "__main__":
    main()
