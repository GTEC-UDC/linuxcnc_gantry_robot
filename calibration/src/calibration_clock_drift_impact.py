"""Effect of the clock drift on the calibration solution.

This script imposes a drift, corrects the time base of the OptiTrack record with it,
re-fits the correction model, and reports what changes in the calibration solution.
"""

import argparse
from typing import cast

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy as scp
from data import (
    CalibrationConfig,
    CalibrationParams,
    design_matrix,
    get_processed_data,
)
from estimate_calibration_clock_drift import GAN_COLS, RB_COLS, rms3d, time_shifted


def fit_correction(
    time: npt.NDArray[np.float64],
    gantry: npt.NDArray[np.float64],
    optitrack: npt.NDArray[np.float64],
    dt: float,
    drift: float,
    t_ref: float,
    correct: bool = True,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.bool_]]:
    """Re-fit the correction with the OptiTrack time base warped by (dt, drift).

    Returns the fitted coefficients, the residual of the corrected positions, and the
    mask of the samples that survived the warping. Without ``correct``, no correction
    is fit, and the residual is the raw discrepancy between the gantry and OptiTrack
    positions, so the drift cannot be absorbed into any free parameter.
    """
    warped = time_shifted(time, optitrack, dt, drift, t_ref)
    mask = cast(npt.NDArray[np.bool_], ~np.isnan(warped).any(axis=1))
    if correct:
        design = design_matrix(gantry[mask])
        coef, _, _, _ = np.linalg.lstsq(design, warped[mask], rcond=None)
        coef = cast(npt.NDArray[np.float64], coef)
        residual = design @ coef - warped[mask]
    else:
        coef = cast(npt.NDArray[np.float64], np.eye(3))
        residual = gantry[mask] - warped[mask]
    return coef, residual, mask


def fit_offset(
    time: npt.NDArray[np.float64],
    gantry: npt.NDArray[np.float64],
    optitrack: npt.NDArray[np.float64],
    drift: float,
    t_ref: float,
    correct: bool = True,
) -> float:
    """Best time offset for a given drift, so the scan is not biased by a fixed one."""
    res = scp.optimize.minimize_scalar(
        lambda dt: rms3d(
            fit_correction(time, gantry, optitrack, dt, drift, t_ref, correct)[1]
        ),
        bounds=(-0.3, 0.3),
        method="bounded",
    )
    return float(res.x)


def describe(label: str, err: npt.NDArray[np.float64]) -> None:
    sigma = err.std(axis=0, ddof=1)
    dist = np.linalg.norm(err, axis=1)
    print(f"  {label}")
    print(f"    per-axis sigma  {sigma[0]:.3f} {sigma[1]:.3f} {sigma[2]:.3f} mm")
    print(f"    3D RMS          {rms3d(err):.3f} mm")
    print(
        f"    median, P95     {np.median(dist):.3f}, {np.percentile(dist, 95):.3f} mm"
    )


def main(args: argparse.Namespace) -> None:
    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.correction.skip_samples.enabled = args.skip_samples
    config.correction.reject_samples.enabled = args.skip_samples
    config.alignment.minimize_options.display = False
    config.correction.minimize_options.display = False

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    data: pd.DataFrame = df.loc[:, ["time"] + RB_COLS + GAN_COLS].dropna()
    time = data["time"].to_numpy()
    optitrack = data[RB_COLS].to_numpy()
    gantry = data[GAN_COLS].to_numpy()
    t_ref = float(time.mean())
    span = time[-1] - time[0]

    speed_all = np.linalg.norm(np.gradient(gantry, time, axis=0), axis=1)
    speed = float(np.median(speed_all[speed_all > 20]))
    print(
        f"capture {span:.0f} s, {len(time)} paired samples, "
        f"median speed while moving {speed:.1f} mm/s"
    )

    # ---------------------------------------------------------------------
    # 1. Positioning residual as a function of the imposed drift
    # ---------------------------------------------------------------------

    print(
        "\nresidual of the corrected positions vs imposed drift "
        f"(offset{' and correction' if args.correct else ''} refitted at each point)"
    )
    print("  drift_ppm    dt_ms   RMS3D_mm   sigma_X  sigma_Y  sigma_Z")
    grid = np.arange(args.scan_from, args.scan_to + args.scan_step / 2, args.scan_step)
    best_drift, best_rms = 0.0, np.inf
    for drift_ppm in grid:
        drift = drift_ppm * 1e-6
        dt = fit_offset(time, gantry, optitrack, drift, t_ref, args.correct)
        err = fit_correction(time, gantry, optitrack, dt, drift, t_ref, args.correct)[1]
        sigma = err.std(axis=0, ddof=1)
        print(
            f"  {drift_ppm:+9.1f} {dt * 1e3:+8.2f} {rms3d(err):10.3f}   "
            f"{sigma[0]:7.3f} {sigma[1]:8.3f} {sigma[2]:8.3f}"
        )
        if rms3d(err) < best_rms:
            best_drift, best_rms = drift_ppm, rms3d(err)

    res = scp.optimize.minimize(
        lambda x: rms3d(
            fit_correction(
                time, gantry, optitrack, x[0], x[1] * 1e-6, t_ref, args.correct
            )[1]
        ),
        x0=np.array([0.0, best_drift]),
        method="Powell",
        tol=1e-12,
    )
    dt_fit, drift_fit = float(res.x[0]), float(res.x[1])
    print(
        f"\njoint fit on positions: offset {dt_fit * 1e3:+.2f} ms, "
        f"drift {drift_fit:+.2f} ppm "
        f"({drift_fit * 1e-6 * span * 1e3:+.2f} ms over the capture, "
        f"{abs(drift_fit) * 1e-6 * span * speed:.2f} mm at {speed:.0f} mm/s)"
    )

    # ---------------------------------------------------------------------
    # 2. Effect on the calibration solution
    # ---------------------------------------------------------------------

    drift = (args.drift if args.drift is not None else drift_fit) * 1e-6
    dt = fit_offset(time, gantry, optitrack, drift, t_ref, args.correct)
    print(
        f"\nsolution with a drift of {drift * 1e6:+.2f} ppm (offset {dt * 1e3:+.2f} ms)"
    )

    coef_ref, err_ref, _ = fit_correction(
        time, gantry, optitrack, 0.0, 0.0, t_ref, args.correct
    )
    coef_drift, err_drift, _ = fit_correction(
        time, gantry, optitrack, dt, drift, t_ref, args.correct
    )

    describe("without the drift", err_ref)
    describe("with the drift", err_drift)

    # Difference between the two forward maps over the positions actually visited
    design = design_matrix(gantry) if args.correct else gantry
    diff = design @ coef_ref - design @ coef_drift
    print("  difference between the two forward maps over the capture")
    print(
        f"    per-axis RMS    {np.sqrt((diff**2).mean(axis=0))[0]:.3f} "
        f"{np.sqrt((diff**2).mean(axis=0))[1]:.3f} "
        f"{np.sqrt((diff**2).mean(axis=0))[2]:.3f} mm"
    )
    print(
        f"    3D RMS, max     {rms3d(diff):.3f}, "
        f"{np.linalg.norm(diff, axis=1).max():.3f} mm"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Check the effect of a clock drift on the positioning residual and on "
            "the fitted correction parameters"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to Optitrack CSV file",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to Gantry CSV file",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to the calibration configuration file",
    )

    parser.add_argument(
        "--calibration",
        type=str,
        default="calibration.json",
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
        help=(
            "Fit a non-linear correction model at each candidate drift. With "
            "--no-correct, the residual is the raw gantry/OptiTrack discrepancy, so "
            "the drift cannot be absorbed into a correction parameter"
        ),
    )

    parser.add_argument(
        "--drift",
        type=float,
        default=None,
        help=(
            "Drift in ppm to evaluate the calibration solution with, typically the "
            "one estimated by estimate_clock_drift.py. Defaults to the value that "
            "minimizes the positioning residual"
        ),
    )

    parser.add_argument(
        "--scan-from",
        type=float,
        default=-70.0,
        help="First drift of the scan, in ppm",
    )

    parser.add_argument(
        "--scan-to",
        type=float,
        default=20.0,
        help="Last drift of the scan, in ppm",
    )

    parser.add_argument(
        "--scan-step",
        type=float,
        default=5.0,
        help="Step of the scan, in ppm",
    )

    main(parser.parse_args())
