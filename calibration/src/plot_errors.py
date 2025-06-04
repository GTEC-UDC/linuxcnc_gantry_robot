# Plot the errors between the rigid body markers and the raw markers

import argparse
from typing import Optional
import logging

import matplotlib.pyplot as plt

from argutils import parse_limit
from data import get_processed_data, load_bad_frames


def plot_errors(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    alignment_file: str = "alignment_params.npy",
    calibration_file: str = "calibration_params.npy",
    calibrate: bool = True,
    bad_frames_file: str = "bad_frames.json",
    remove_bad_frames: bool = False,
    time_limit: Optional[tuple[float, float]] = None,
    position_limit: Optional[tuple[float, float]] = None,
    error_limit: Optional[tuple[float, float]] = None,
    abs_error_limit: Optional[tuple[float, float]] = None,
) -> tuple[plt.Axes, plt.Axes, plt.Axes, plt.Axes, plt.Axes]:
    """Plot gantry and optitrack position and error data.

    Args:
        gantry_file: Path to gantry CSV file
        optitrack_file: Path to Optitrack CSV file
        alignment_file: Path to alignment parameters file
        calibration_file: Path to calibration parameters file
        remove_bad_frames: Whether to remove bad frames from the data
        bad_frames_file: Path to file with bad frames ranges
        time_limit: Optional (min, max) tuple for x-axis time limits (seconds)
        position_limit: Optional (min, max) tuple for position plot y-axis limits (mm)
        error_limit: Optional (min, max) tuple for error plots y-axis limits (mm)
    """
    # Handle bad frames if needed
    bad_frames = None
    if remove_bad_frames:
        bad_frames = load_bad_frames(bad_frames_file)

    # Get the processed data
    df, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        alignment_file,
        calibration_file,
        bad_frames=bad_frames,
        calibrate=calibrate,
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
    sep = ".CALIBRATED." if calibrate else "."

    # Plot all positions in the same subplot
    ax_pos.plot(df["time"], df[f"GAN{sep}X"], "b-", linewidth=0.5, label="Gantry X")
    ax_pos.plot(df["time"], df[f"GAN{sep}Y"], "g-", linewidth=0.5, label="Gantry Y")
    ax_pos.plot(df["time"], df[f"GAN{sep}Z"], "r-", linewidth=0.5, label="Gantry Z")

    # Add labels for position plot
    ax_pos.set_ylabel("Position (mm)")
    ax_pos.legend()

    # Plot differences over time
    ax_x_err.plot(df["time"], df[f"GAN.ERR{sep}X"], "b-", linewidth=0.5, label="X Error")
    ax_y_err.plot(df["time"], df[f"GAN.ERR{sep}Y"], "g-", linewidth=0.5, label="Y Error")
    ax_z_err.plot(df["time"], df[f"GAN.ERR{sep}Z"], "r-", linewidth=0.5, label="Z Error")
    ax_abs_err.plot(
        df["time"], df[f"GAN.ERR{sep}Abs"], "k-", linewidth=0.5, label="Absolute Error"
    )

    # Set labels
    ax_x_err.set_ylabel("X Error (mm)")
    ax_y_err.set_ylabel("Y Error (mm)")
    ax_z_err.set_ylabel("Z Error (mm)")
    ax_abs_err.set_ylabel("Absolute Error (mm)")
    ax_abs_err.set_xlabel("Time (s)")

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
        description="Plot gantry and optitrack error data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to the CSV file with the Optitrack movement data",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to the CSV file with the gantry movement data",
    )

    parser.add_argument(
        "--alignment",
        type=str,
        default="alignment_params.npy",
        help="Path to alignment parameters file",
    )

    parser.add_argument(
        "--calibrate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Calibrate the Gantry data",
    )

    parser.add_argument(
        "--calibration",
        type=str,
        default="calibration_params.npy",
        help="Path to calibration parameters file",
    )

    parser.add_argument(
        "--remove-bad-frames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Remove bad frames from the data",
    )

    parser.add_argument(
        "--bad-frames",
        type=str,
        default="bad_frames.json",
        help="Path to file of bad frames data",
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
        default="0,15",
        help="Y-axis limit for absolute error plot as 'min,max' (mm)",
    )

    args = parser.parse_args()

    plot_errors(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        alignment_file=args.alignment,
        calibration_file=args.calibration,
        calibrate=args.calibrate,
        remove_bad_frames=args.remove_bad_frames,
        bad_frames_file=args.bad_frames,
        time_limit=args.time_limit,
        position_limit=args.poslim,
        error_limit=args.errlim,
        abs_error_limit=args.abserrlim,
    )


if __name__ == "__main__":
    main()
