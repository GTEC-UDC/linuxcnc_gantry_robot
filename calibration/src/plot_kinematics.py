"""Plot the position, velocity and acceleration in the calibration measurement.

The velocity and the acceleration of the gantry and of the platform measured by
OptiTrack are computed with a Savitzky-Golay filter.
The script prints their maximum values over the capture and plots the three
quantities along each axis over time.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from argutils import parse_limit
from data import (
    ERR_COLS_CALIBRATED,
    GAN_COLS,
    RB_COLS,
    CalibrationConfig,
    CalibrationParams,
    fill_gaps,
    get_processed_data,
)
from defaults import CALIBRATION_FILE, CONFIG_FILE, GANTRY_FILE, OPTITRACK_FILE
from scipy.ndimage import binary_dilation
from scipy.signal import savgol_filter

Array = npt.NDArray[np.float64]


def window_length(rate: float, smooth: float) -> int:
    """Number of samples of the filter window, an odd value."""
    return round(smooth * rate) | 1


def derivative(pos: Array, rate: float, smooth: float, order: int, degree: int) -> Array:
    """Derivative of a track, from a Savitzky-Golay filter.

    Fits a polynomial of degree ``degree`` in a window of ``smooth`` seconds
    around each sample and takes the derivative of the fit.
    """
    window = window_length(rate, smooth)

    return savgol_filter(
        pos, window_length=window, polyorder=degree, deriv=order, delta=1 / rate, axis=0
    )


def print_maximum(label: str, unit: str, of_gantry: Array, of_optitrack: Array) -> None:
    """Maximum absolute value along each axis and maximum norm."""
    print(f"\nmaximum {label} ({unit})")

    for source, values in [("gantry", of_gantry), ("OptiTrack", of_optitrack)]:
        axes = np.abs(values).max(axis=0)
        norm = np.linalg.norm(values, axis=1).max()
        print(
            f"  {source:10s} norm {norm:8.1f} "
            f"(X {axes[0]:.1f}, Y {axes[1]:.1f}, Z {axes[2]:.1f})"
        )


def main(args: argparse.Namespace) -> None:
    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.correction.skip_samples.enabled = args.skip_samples
    config.correction.reject_samples.enabled = args.skip_samples
    config.alignment.minimize_options.display = False

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    # OptiTrack frame time and rate
    time = df["time"].to_numpy()
    rate = (len(time) - 1) / (time[-1] - time[0])

    # Samples that are not filled in the residual
    _, gap = fill_gaps(df[ERR_COLS_CALIBRATED].to_numpy())
    kept = ~gap

    # Samples whose filter window does not reach a filled sample
    half_window = window_length(rate, args.smooth) // 2
    valid = ~binary_dilation(gap, iterations=half_window)

    # Position, velocity and acceleration of the gantry and of the platform
    gantry, _ = fill_gaps(df[GAN_COLS].to_numpy())
    optitrack, _ = fill_gaps(df[RB_COLS].to_numpy())

    v_gantry = derivative(gantry, rate, args.smooth, 1, args.degree)
    v_optitrack = derivative(optitrack, rate, args.smooth, 1, args.degree)

    a_gantry = derivative(gantry, rate, args.smooth, 2, args.degree)
    a_optitrack = derivative(optitrack, rate, args.smooth, 2, args.degree)

    print(
        f"capture {time[-1] - time[0]:.0f} s at {rate:.2f} Hz, "
        f"{kept.sum()} of {len(time)} samples kept, "
        f"{valid.sum()} with the filter window inside the kept samples"
    )

    print(
        f"Savitzky-Golay filter of {args.smooth:g} s and degree {args.degree}, "
        "over the samples with the window inside the kept samples"
    )

    print_maximum("velocity", "mm/s", v_gantry[valid], v_optitrack[valid])
    print_maximum("acceleration", "mm/s^2", a_gantry[valid], a_optitrack[valid])

    if not args.plot:
        return

    # Vector of kept samples inside the time limits
    in_limits = np.ones_like(kept)
    if args.time_limit is not None:
        in_limits = (time >= args.time_limit[0]) & (time <= args.time_limit[1])

    # One row per axis; position, velocity and acceleration in the columns
    _, axes = plt.subplots(3, 3, sharex=True, figsize=(16, 8))
    columns = [
        ("Position (mm)", gantry, optitrack, kept & in_limits),
        ("Velocity (mm/s)", v_gantry, v_optitrack, valid & in_limits),
        ("Acceleration (mm/s$^2$)", a_gantry, a_optitrack, valid & in_limits),
    ]

    for col, (quantity, of_gantry, of_optitrack, shown) in enumerate(columns):
        for axis in range(3):
            ax = axes[axis, col]
            gantry_shown = np.where(shown, of_gantry[:, axis], np.nan)
            optitrack_shown = np.where(shown, of_optitrack[:, axis], np.nan)
            ax.plot(time, gantry_shown, lw=0.8, label="gantry")
            ax.plot(time, optitrack_shown, lw=0.8, label="OptiTrack")
            ax.set_ylabel(f"{'XYZ'[axis]} {quantity}")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper right")

    axes[0, 1].set_title(
        f"Savitzky-Golay filter of {args.smooth:g} s and degree {args.degree}"
    )

    for ax in axes[-1]:
        ax.set_xlabel("Time (s)")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Plot the position, velocity and acceleration of the gantry and of the "
            "platform measured by OptiTrack in the calibration measurement"
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
        "--smooth",
        type=float,
        default=1.0,
        help="Savitzky-Golay window for the velocity and the acceleration, in seconds",
    )

    parser.add_argument(
        "--degree",
        type=int,
        default=2,
        help="Degree of the Savitzky-Golay polynomial",
    )

    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plot the position, velocity and acceleration over time",
    )

    parser.add_argument(
        "--time-limit",
        type=parse_limit,
        default=None,
        help="Time limits of the plots, in seconds, as 'min,max'",
    )

    main(parser.parse_args())
