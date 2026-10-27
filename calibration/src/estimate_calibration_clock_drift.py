"""Estimate the residual clock drift between the gantry and the OptiTrack records.

The alignment of ``get_processed_data`` removes a constant offset between the two
clocks. If the clocks also run at slightly different rates, the offset left after
that alignment grows linearly with time. This script estimates that residual drift by
applying an affine transformation to the time base of the OptiTrack record,

    t -> t - (dt + drift * (t - t_ref)),

so the residual offset equals dt at t_ref and grows linearly away from it at the
drift rate. t_ref is the reference instant around which that offset is measured, taken
as the mean time of the window being fit. The script looks for the pair (dt, drift)
that minimizes the mean squared difference between the two records, in the same way
the alignment parameters are fitted in ``data.py``.

The comparison is made on velocity, not on position. A positioning residual mixes the
timing error with the geometric deviation of the gantry: a scale error, or any smooth
position-dependent deviation left by the correction model, produces a residual along
the direction of travel that is indistinguishable from a time offset. Velocity avoids
that, and to remove any remaining scale or linear mismatch a free 3x3 matrix mapping
the gantry velocity onto the measured one is re-estimated by least squares for
every candidate pair, so only the timing is left for (dt, drift) to explain.
"""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy as scp
from data import (
    GAN_COLS,
    GAN_COLS_CALIBRATED,
    RB_COLS,
    CalibrationConfig,
    CalibrationParams,
    fill_gaps,
    get_processed_data,
    rms3d,
)
from defaults import CALIBRATION_FILE, CONFIG_FILE, GANTRY_FILE, OPTITRACK_FILE
from scipy.signal import savgol_filter

Array = npt.NDArray[np.float64]

logger = logging.getLogger(__name__)


def velocity(time: Array, pos: Array, smooth: float, rate: float) -> Array:
    """Velocity of a track, from a Savitzky-Golay derivative filter.

    Fitting a local polynomial and reading off its derivative avoids the noise
    amplification of a raw finite difference. ``time`` is assumed evenly spaced, as
    it is the native OptiTrack clock (the gantry log is already resampled onto it in
    ``get_processed_data``). The same filter is applied to both records, so it does
    not bias their relative timing.
    """
    width = max(int(smooth * rate) | 1, 5)
    return savgol_filter(
        pos, window_length=width, polyorder=4, deriv=1, delta=1 / rate, axis=0
    )


def time_shifted(
    time: Array, values: Array, dt: float, drift: float, t_ref: float
) -> Array:
    """Resample a signal with an affine transformation of its time base."""
    shifted = time - (dt + drift * (time - t_ref))
    return np.column_stack(
        [
            np.interp(shifted, time, values[:, k], left=np.nan, right=np.nan)
            for k in range(3)
        ]
    )


def velocity_residual(
    time: Array,
    v_gantry: Array,
    v_optitrack: Array,
    dt: float,
    drift: float,
    t_ref: float,
    fit_matrix: bool = True,
) -> Array:
    """Velocity mismatch for a given time transformation, in mm/s.

    With ``fit_matrix``, the linear map from the gantry velocity to the measured one
    is re-estimated by least squares, which absorbs any scale or linear mismatch
    between the two records.
    """
    o = time_shifted(time, v_optitrack, dt, drift, t_ref)
    mask = ~np.isnan(o).any(axis=1)
    g = v_gantry[mask]
    if fit_matrix:
        params, _, _, _ = np.linalg.lstsq(g, o[mask], rcond=None)
        g = g @ params
    return o[mask] - g


def fit_drift(
    time: Array,
    v_gantry: Array,
    v_optitrack: Array,
    fit_matrix: bool = True,
    display: bool = False,
) -> tuple[float, float, float, float]:
    """
    Fit the time offset and the drift.
    Returns (dt, drift_ppm, rms_before, rms_after).
    """
    t_ref = float(time.mean())

    def objective(x: Array) -> float:
        err = velocity_residual(
            time, v_gantry, v_optitrack, x[0], x[1] * 1e-6, t_ref, fit_matrix
        )
        if len(err) < 0.5 * len(time):  # the shift pushed too much data out of range
            return np.inf
        return float((err**2).sum(axis=1).mean())

    rms_before = rms3d(
        velocity_residual(time, v_gantry, v_optitrack, 0.0, 0.0, t_ref, fit_matrix)
    )
    res = scp.optimize.minimize(
        objective,
        x0=np.zeros(2),
        method="Powell",
        tol=1e-12,
        options={"disp": display},
    )

    if not res.success:
        logger.warning("The drift fit did not converge: %s", res.message)

    dt, drift_ppm = float(res.x[0]), float(res.x[1])
    rms_after = rms3d(
        velocity_residual(
            time, v_gantry, v_optitrack, dt, drift_ppm * 1e-6, t_ref, fit_matrix
        )
    )

    return dt, drift_ppm, rms_before, rms_after


def report(
    label: str,
    time: Array,
    v_gantry: Array,
    v_optitrack: Array,
    speed: float,
    fit_matrix: bool = True,
) -> tuple[float, float]:
    dt, drift, rms_before, rms_after = fit_drift(
        time, v_gantry, v_optitrack, fit_matrix
    )
    span = time[-1] - time[0]
    print(f"\n{label} ({len(time)} samples, {span:.0f} s)")
    print(f"  time offset       {dt * 1e3:+8.2f} ms")
    print(
        f"  drift             {drift:+8.2f} ppm "
        f"({drift * 1e-6 * span * 1e3:+.2f} ms over the interval)"
    )
    print(f"  velocity residual {rms_before:.2f} -> {rms_after:.2f} mm/s")
    print(
        f"  at {speed:.0f} mm/s the drift spans "
        f"{abs(drift) * 1e-6 * span * speed:.3f} mm "
        f"({abs(drift) * 1e-6 * span / 2 * speed:.3f} mm about its mean)"
    )
    return dt, drift


def drift_profile(
    time: Array, v_gantry: Array, v_optitrack: Array, values_ppm: Array
) -> None:
    """Velocity residual as a function of the imposed drift, offset refitted."""
    t_ref = float(time.mean())
    print("\ndrift profile (offset and matrix refitted at each point)")
    print("  drift_ppm    dt_ms   rms_mm_s")

    def objective(shift: float, drift: float) -> float:
        err = velocity_residual(time, v_gantry, v_optitrack, shift, drift, t_ref)
        return float((err**2).sum(axis=1).mean())

    for d in values_ppm:
        drift = float(d) * 1e-6
        res = scp.optimize.minimize_scalar(
            objective,
            args=(drift,),
            bounds=(-0.5, 0.5),
            method="bounded",
        )
        if not res.success:
            logger.warning("The offset fit did not converge: %s", res.message)
        err = velocity_residual(
            time, v_gantry, v_optitrack, float(res.x), d * 1e-6, t_ref
        )
        print(f"  {d:+9.1f} {float(res.x) * 1e3:+8.2f} {rms3d(err):10.3f}")


def plot_velocities(time: Array, v_gantry: Array, v_optitrack: Array) -> None:
    """Plot the gantry and OptiTrack velocity components over time."""
    _, axes = plt.subplots(4, 1, sharex=True, figsize=(10, 8))

    for ax, label, g, o in zip(
        axes,
        ["X", "Y", "Z", "|v|"],
        [
            v_gantry[:, 0],
            v_gantry[:, 1],
            v_gantry[:, 2],
            np.linalg.norm(v_gantry, axis=1),
        ],
        [
            v_optitrack[:, 0],
            v_optitrack[:, 1],
            v_optitrack[:, 2],
            np.linalg.norm(v_optitrack, axis=1),
        ],
    ):
        ax.plot(time, g, "b-", linewidth=0.5, label="Gantry")
        ax.plot(time, o, "r-", linewidth=0.5, label="OptiTrack")
        ax.set_ylabel(f"{label} vel. (mm/s)")
        ax.grid(True)
        ax.legend()

    axes[-1].set_xlabel("Time (s)")
    plt.tight_layout()
    plt.show()


def main(args: argparse.Namespace) -> None:
    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.correction.skip_samples.enabled = args.skip_samples
    config.correction.reject_samples.enabled = args.skip_samples
    config.correction.enabled = args.correct
    config.alignment.minimize_options.display = False

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    gan_cols = GAN_COLS_CALIBRATED if args.correct else GAN_COLS
    data: pd.DataFrame = df.loc[:, ["time"] + RB_COLS + gan_cols]
    data = data.rename(columns=dict(zip(gan_cols, GAN_COLS)))
    time = data["time"].to_numpy()
    rate = 1.0 / float(np.median(np.diff(time)))

    rb_pos, gap_rb = fill_gaps(data[RB_COLS].to_numpy())
    gan_pos, gap_gan = fill_gaps(data[GAN_COLS].to_numpy())

    v_optitrack = velocity(time, rb_pos, args.smooth, rate)
    v_gantry = velocity(time, gan_pos, args.smooth, rate)

    # Drop the points fill_gaps had to fabricate across a gap, now that the filter
    # has already run with the filled-in data as context.
    valid = ~(gap_rb | gap_gan)
    time, v_gantry, v_optitrack = time[valid], v_gantry[valid], v_optitrack[valid]

    if args.inject:
        # Warp the OptiTrack time base by a known amount, to check that the fit
        # recovers it. The fit should return -inject.
        v_optitrack = time_shifted(
            time, v_optitrack, 0.0, args.inject * 1e-6, float(time.mean())
        )
        keep = ~np.isnan(v_optitrack).any(axis=1)
        time, v_optitrack, v_gantry = time[keep], v_optitrack[keep], v_gantry[keep]
        print(f"injected drift: {args.inject:+.2f} ppm")

    s = np.linalg.norm(v_gantry, axis=1)
    speed = float(np.median(s[s > 20]))
    print(
        f"capture {time[-1] - time[0]:.0f} s, {len(time)} paired samples at "
        f"{rate:.1f} Hz, smoothing {args.smooth:.2f} s"
    )
    print(f"median speed while moving: {speed:.1f} mm/s")

    report("whole capture", time, v_gantry, v_optitrack, speed)
    report(
        "whole capture, no velocity matrix",
        time,
        v_gantry,
        v_optitrack,
        speed,
        fit_matrix=False,
    )

    # Independent sub-intervals: a real clock skew gives the same drift in all of them
    edges = np.linspace(0, len(time), args.splits + 1).astype(int)
    for i in range(args.splits):
        sl = slice(edges[i], edges[i + 1])
        report(
            f"segment {i + 1}/{args.splits}",
            time[sl],
            v_gantry[sl],
            v_optitrack[sl],
            speed,
            fit_matrix=False,
        )

    if args.profile:
        drift_profile(time, v_gantry, v_optitrack, np.arange(-60, 61, 15.0))

    if args.plot:
        plot_velocities(time, v_gantry, v_optitrack)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the residual clock drift between the gantry and OptiTrack "
            "records by aligning their velocity profiles in time"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=Path,
        default=OPTITRACK_FILE,
        help="Path to Optitrack CSV file",
    )

    parser.add_argument(
        "--gantry",
        type=Path,
        default=GANTRY_FILE,
        help="Path to Gantry CSV file",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_FILE,
        help="Path to the calibration configuration file",
    )

    parser.add_argument(
        "--calibration",
        type=Path,
        default=CALIBRATION_FILE,
        help="Path to the calibration parameters file",
    )

    parser.add_argument(
        "--skip-samples",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the sample exclusions of the configuration file",
    )

    parser.add_argument(
        "--correct",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the non-linear coordinate correction step",
    )

    parser.add_argument(
        "--smooth",
        type=float,
        default=1.0,
        help=(
            "Width of the Savitzky-Golay window used to differentiate position into "
            "velocity, in seconds. Windows below about half a second leave too much "
            "differentiation noise for the fit to resolve the drift"
        ),
    )

    parser.add_argument(
        "--splits",
        type=int,
        default=4,
        help="Number of sub-intervals fitted independently as a consistency check",
    )

    parser.add_argument(
        "--inject",
        type=float,
        default=0.0,
        help=(
            "Warp the OptiTrack time base by this drift, in ppm, before fitting, "
            "to check that the fit recovers it"
        ),
    )

    parser.add_argument(
        "--profile",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print the residual as a function of the imposed drift",
    )

    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Plot the gantry and OptiTrack velocity curves over time",
    )

    main(parser.parse_args())
