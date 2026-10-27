"""Check oscillations of the platform in the calibration measurement.

The accelerations of the gantry may create an oscillation in the structure.
OptiTrack would see it, so it would be in the residual between the corrected
gantry position and the OptiTrack position, at frequencies above those of the
motion.

To check its effect, the residual is filtered with a low-pass filter, which
removes the higher frequencies, and the combined standard uncertainty u_c (3D RMS
of the residual) is computed with and without the filter. If an oscillation had a
significant effect, u_c would drop with the filter.

This script has three plots:

- ``--plot-psd``: power spectral density (PSD) of the residual along each axis.
- ``--plot-residual``: residual along each axis over time, with and without the
  low-pass filter.
- ``--plot-time``: velocity and acceleration of the gantry and of the platform
  measured by OptiTrack, along each axis, over time.
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
    rms3d,
)
from defaults import CALIBRATION_FILE, CONFIG_FILE, GANTRY_FILE, OPTITRACK_FILE
from scipy.signal import butter, savgol_filter, sosfiltfilt, welch

Array = npt.NDArray[np.float64]


def derivative(
    pos: Array, rate: float, smooth: float, order: int, degree: int = 4
) -> Array:
    """Derivative of a track, from a Savitzky-Golay filter.

    Fits a polynomial of degree ``degree`` in a window of ``smooth`` seconds
    around each sample and takes the derivative of the fit.
    """
    window = round(smooth * rate) | 1  # `| 1` is used to get an odd value

    return savgol_filter(
        pos, window_length=window, polyorder=degree, deriv=order, delta=1 / rate, axis=0
    )


def low_pass(signal: Array, rate: float, cutoff: float) -> Array:
    """Signal filtered with a 4th order Butterworth low-pass filter."""
    sos = butter(4, cutoff, btype="lowpass", fs=rate, output="sos")
    return sosfiltfilt(sos, signal, axis=0)


def print_residual(label: str, err: Array) -> None:
    axes = np.sqrt((err**2).mean(axis=0))
    print(
        f"  {label:28s} u_c {rms3d(err):.3f} mm "
        f"(X {axes[0]:.3f}, Y {axes[1]:.3f}, Z {axes[2]:.3f} mm)"
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

    # Residual, with the gaps filled; ``kept`` marks the samples that are not filled
    err, gap = fill_gaps(df[ERR_COLS_CALIBRATED].to_numpy())
    kept = ~gap

    # Velocity and acceleration of the gantry and of the platform
    gantry, _ = fill_gaps(df[GAN_COLS].to_numpy())
    optitrack, _ = fill_gaps(df[RB_COLS].to_numpy())

    v_gantry = derivative(gantry, rate, args.smooth, 1)
    v_optitrack = derivative(optitrack, rate, args.smooth, 1)

    a_gantry = derivative(gantry, rate, args.smooth, 2)
    a_optitrack = derivative(optitrack, rate, args.smooth, 2)

    speed = np.linalg.norm(v_gantry, axis=1)
    moving = kept & (speed > 20)

    print(
        f"capture {time[-1] - time[0]:.0f} s at {rate:.2f} Hz, "
        f"{kept.sum()} of {len(time)} samples kept"
    )

    print(
        f"speed of the gantry while moving: median {np.median(speed[moving]):.0f} mm/s, "
        f"moving {moving.sum() / kept.sum():.1%} of the kept samples"
    )

    # Residual without its frequencies above the cutoff.
    err_filtered = low_pass(err, rate, args.cutoff)

    print("\nresidual (RMS of each axis and u_c, over the kept samples)")
    print_residual("without filter", err[kept])
    print_residual(f"low-pass filter at {args.cutoff:g} Hz", err_filtered[kept])

    if args.plot_psd:
        # Compute PSD using Welch’s method
        first, last = np.flatnonzero(kept)[
            [0, -1]
        ]  # first and last indices where kept = True
        freq, power = welch(
            err[first : last + 1], fs=rate, nperseg=int(args.segment * rate), axis=0
        )

        _, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 8))

        for axis, ax in enumerate(axes):
            ax.semilogy(freq, power[:, axis], lw=0.8)
            ax.axvline(args.cutoff, color="k", ls="--", lw=0.8, label="cutoff")
            ax.set_ylabel(f"PSD {'XYZ'[axis]} (mm$^2$/Hz)")
            ax.grid(True, which="both", alpha=0.4)
            ax.legend(loc="upper right")

        axes[0].set_title(f"PSD of the residual, Welch segments of {args.segment:g} s")
        axes[-1].set_xlabel("Frequency (Hz)")
        axes[-1].set_xlim(0, args.max_freq)
        plt.tight_layout()

    # Only the kept samples inside the time limits are drawn in the time plots, so
    # the vertical axes are scaled to them
    shown = kept.copy()
    if args.time_limit is not None:
        shown &= (time >= args.time_limit[0]) & (time <= args.time_limit[1])

    if args.plot_residual:
        _, axes = plt.subplots(3, 1, sharex=True, figsize=(12, 8))

        for axis, ax in enumerate(axes):
            residual_shown = np.where(shown, err[:, axis], np.nan)
            filtered_shown = np.where(shown, err_filtered[:, axis], np.nan)
            ax.plot(time, residual_shown, lw=0.6, color="0.6", label="residual")
            ax.plot(
                time,
                filtered_shown,
                lw=1.0,
                label=f"low-pass filter at {args.cutoff:g} Hz",
            )
            ax.set_ylabel(f"{'XYZ'[axis]} residual (mm)")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper right")

        axes[-1].set_xlabel("Time (s)")
        plt.tight_layout()

    if args.plot_time:
        # One row per axis; velocity in the left column, acceleration in the right one
        _, axes = plt.subplots(3, 2, sharex=True, figsize=(14, 8))
        columns = [
            ("Velocity (mm/s)", v_gantry, v_optitrack),
            ("Acceleration (mm/s$^2$)", a_gantry, a_optitrack),
        ]

        for col, (quantity, of_gantry, of_optitrack) in enumerate(columns):
            for axis in range(3):
                ax = axes[axis, col]
                gantry_shown = np.where(shown, of_gantry[:, axis], np.nan)
                optitrack_shown = np.where(shown, of_optitrack[:, axis], np.nan)
                ax.plot(time, gantry_shown, lw=0.8, label="gantry")
                ax.plot(time, optitrack_shown, lw=0.8, label="OptiTrack")
                ax.set_ylabel(f"{'XYZ'[axis]} {quantity}")
                ax.grid(True, alpha=0.4)
                ax.legend(loc="upper right")

        axes[0, 0].set_title(f"Savitzky-Golay filter of {args.smooth:g} s")

        for ax in axes[-1]:
            ax.set_xlabel("Time (s)")

        plt.tight_layout()

    if args.plot_psd or args.plot_residual or args.plot_time:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Check the effect of an oscillation of the platform on the residual of "
            "the calibration measurement"
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
        "--cutoff",
        type=float,
        default=1.0,
        help="Cutoff frequency of the low-pass filter of the residual, in Hz",
    )

    parser.add_argument(
        "--plot-psd",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Plot the PSD of the residual along each axis",
    )

    parser.add_argument(
        "--segment",
        type=float,
        default=40.0,
        help="Length of the Welch segments of the PSD, in seconds",
    )

    parser.add_argument(
        "--max-freq",
        type=float,
        default=15.0,
        help="Upper limit of the frequency axis of the PSD plot, in Hz",
    )

    parser.add_argument(
        "--plot-residual",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Plot the residual over time, with and without the low-pass filter",
    )

    parser.add_argument(
        "--plot-time",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Plot the velocity and the acceleration of the gantry and of the platform "
            "measured by OptiTrack over time"
        ),
    )

    parser.add_argument(
        "--smooth",
        type=float,
        default=0.5,
        help="Savitzky-Golay window for the velocity and the acceleration, in seconds",
    )

    parser.add_argument(
        "--time-limit",
        type=parse_limit,
        default=None,
        help="Time limits of the time plots, in seconds, as 'min,max'",
    )

    main(parser.parse_args())
