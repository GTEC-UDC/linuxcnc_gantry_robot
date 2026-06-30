# Plot the errors between the rigid body markers and the raw markers

import argparse
import logging
import os
from typing import Literal, Optional

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
import numpy as np
from argutils import parse_limit
from data import CalibrationConfig, CalibrationParams, get_processed_data
from scipy.signal import savgol_filter


def plot_errors(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    config_file: str = "config.json",
    calibration_file: str = "calibration.json",
    correct: bool = True,
    skip_frames: bool = True,
    time_unit: Literal["s", "frames"] = "s",
    time_limit: Optional[tuple[float, float]] = None,
    position_limit: Optional[tuple[float, float]] = None,
    error_limit: Optional[tuple[float, float]] = None,
    abs_error_limit: Optional[tuple[float, float]] = None,
    show_acceleration: bool = False,
    accel_window: int = 51,
) -> tuple[mpl_axes.Axes, mpl_axes.Axes, mpl_axes.Axes, mpl_axes.Axes, mpl_axes.Axes]:
    """Plot gantry and OptiTrack position and error data.

    Args:
        gantry_file: Path to gantry CSV file
        optitrack_file: Path to OptiTrack CSV file
        alignment_file: Path to alignment parameters file
        calibration_file: Path to calibration parameters file
        remove_bad_frames: Whether to remove bad frames from the data
        bad_frames_file: Path to file with bad frames ranges
        time_unit: Time unit for the x-axis (s, frames)
        time_limit: Optional (min, max) tuple for x-axis time limits (seconds or frames)
        position_limit: Optional (min, max) tuple for position plot y-axis limits (mm)
        error_limit: Optional (min, max) tuple for error plots y-axis limits (mm)
    """

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = CalibrationConfig.model_validate_json(f.read())
            print("Loaded calibration configuration from", config_file)
    else:
        config = CalibrationConfig()
        print("No calibration configuration file found. Using default configuration.")

    with open(calibration_file, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())
        print("Loaded calibration parameters from", calibration_file)

    # Override the configuration with the provided arguments
    config.correction.enabled = correct
    config.skip_frames.enabled = skip_frames

    # Get the processed data
    df, _, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        config=config,
        calibration_params=calibration_params,
    )

    # Create figure with subplots
    plt.figure(figsize=(10, 8))

    # Create five subplots: 1 for positions, 4 for errors
    ax_pos = plt.subplot(5, 1, 1)
    ax_x_err = plt.subplot(5, 1, 2)
    ax_y_err = plt.subplot(5, 1, 3)
    ax_z_err = plt.subplot(5, 1, 4)
    ax_abs_err = plt.subplot(5, 1, 5)

    # Enable grid for all subplots
    for ax in [ax_pos, ax_x_err, ax_y_err, ax_z_err, ax_abs_err]:
        ax.grid(True)

    # String separator for the gantry coordinates
    sep = ".CALIBRATED." if correct else "."

    # Compute acceleration from gantry positions (mm/s²) using a Savitzky-Golay
    # filter to suppress noise amplification from double differentiation.
    if show_acceleration:
        dt = float(df["time"].diff().median())
        for coord in ["X", "Y", "Z"]:
            pos = df[f"GAN{sep}{coord}"].copy()
            nan_mask = pos.isna().to_numpy()

            pos_filled = (
                pos.interpolate(method="linear", limit_area="inside")
                .ffill()
                .bfill()
                .to_numpy(dtype=float)
            )

            acc = savgol_filter(
                pos_filled, window_length=accel_window, polyorder=3, deriv=2, delta=dt
            )

            acc[nan_mask] = np.nan
            df["GAN.ACC." + coord] = acc
        df["GAN.ACC.Abs"] = np.sqrt(
            df["GAN.ACC.X"] ** 2 + df["GAN.ACC.Y"] ** 2 + df["GAN.ACC.Z"] ** 2
        )

    # Select the time column based on the time unit
    time_data = df["time"] if time_unit == "s" else df["frame"]

    # Plot all positions in the same subplot
    ax_pos.plot(time_data, df[f"GAN{sep}X"], "b-", linewidth=0.5, label="Gantry X")
    ax_pos.plot(time_data, df[f"GAN{sep}Y"], "g-", linewidth=0.5, label="Gantry Y")
    ax_pos.plot(time_data, df[f"GAN{sep}Z"], "r-", linewidth=0.5, label="Gantry Z")

    # Add labels for position plot
    ax_pos.set_ylabel("Position (mm)")
    ax_pos.legend()

    # Plot differences over time
    ax_x_err.plot(time_data, df[f"GAN.ERR{sep}X"], "b-", linewidth=0.5, label="X Error")
    ax_y_err.plot(time_data, df[f"GAN.ERR{sep}Y"], "g-", linewidth=0.5, label="Y Error")
    ax_z_err.plot(time_data, df[f"GAN.ERR{sep}Z"], "r-", linewidth=0.5, label="Z Error")
    ax_abs_err.plot(
        time_data, df[f"GAN.ERR{sep}Abs"], "k-", linewidth=0.5, label="Absolute Error"
    )

    # Overlay acceleration on each error subplot
    if show_acceleration:
        for ax, coord, acc_label in [
            (ax_x_err, "X", "X Accel"),
            (ax_y_err, "Y", "Y Accel"),
            (ax_z_err, "Z", "Z Accel"),
            (ax_abs_err, "Abs", "|Accel|"),
        ]:
            ax_twin = ax.twinx()
            ax_twin.plot(
                time_data,
                df["GAN.ACC." + coord],
                color="tab:purple",
                linewidth=1,
                label=acc_label,
            )
            ax_twin.set_ylabel("Acc. (mm/s²)")
            ax_twin.tick_params(axis="y")

    # Set labels
    ax_x_err.set_ylabel("X Error (mm)")
    ax_y_err.set_ylabel("Y Error (mm)")
    ax_z_err.set_ylabel("Z Error (mm)")
    ax_abs_err.set_ylabel("Absolute Error (mm)")
    ax_abs_err.set_xlabel(f"Time ({time_unit})")

    # Set time limits
    if time_limit is not None:
        for ax in [ax_pos, ax_x_err, ax_y_err, ax_z_err, ax_abs_err]:
            ax.set_xlim(*time_limit)

    # Set position limits
    if position_limit is not None:
        ax_pos.set_ylim(*position_limit)

    # Set error limits
    if error_limit:
        for ax in [ax_x_err, ax_y_err, ax_z_err]:
            ax.set_ylim(*error_limit)

    if abs_error_limit:
        ax_abs_err.set_ylim(*abs_error_limit)

    plt.tight_layout()
    plt.show()

    return ax_pos, ax_x_err, ax_y_err, ax_z_err, ax_abs_err


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Plot gantry and OptiTrack error data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to the CSV file with the OptiTrack movement data",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to the CSV file with the gantry movement data",
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
        "--correct",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the non-linear coordinate correction step",
    )

    parser.add_argument(
        "--skip-frames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable skipping the frames set in the configuration file",
    )

    parser.add_argument(
        "--time-unit",
        type=str,
        choices=["s", "frames"],
        default="s",
        help="Time unit for the x-axis (s, frames)",
    )

    parser.add_argument(
        "--time-limit",
        type=parse_limit,
        default=None,
        help="Time limit for x-axis as 'min,max' (seconds)",
    )

    parser.add_argument(
        "--poslim",
        type=parse_limit,
        default=None,
        help="Y-axis limit for position plot as 'min,max' (mm)",
    )

    parser.add_argument(
        "--errlim",
        type=parse_limit,
        default="-15,15",
        help="Y-axis limit for X, Y, and Z error plots as 'min,max' (mm)",
    )

    parser.add_argument(
        "--abserrlim",
        type=parse_limit,
        default="0,20",
        help="Y-axis limit for absolute error plot as 'min,max' (mm)",
    )

    parser.add_argument(
        "--acceleration",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Overlay gantry acceleration on each error subplot (right y-axis)",
    )

    parser.add_argument(
        "--accel-window",
        type=int,
        default=51,
        help="Savitzky-Golay window length for acceleration smoothing; must be odd",
    )

    args = parser.parse_args()

    plot_errors(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        config_file=args.config,
        calibration_file=args.calibration,
        correct=args.correct,
        skip_frames=args.skip_frames,
        time_unit=args.time_unit,
        time_limit=args.time_limit,
        position_limit=args.poslim,
        error_limit=args.errlim,
        abs_error_limit=args.abserrlim,
        show_acceleration=args.acceleration,
        accel_window=args.accel_window,
    )


if __name__ == "__main__":
    main()
