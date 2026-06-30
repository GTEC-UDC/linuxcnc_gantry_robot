import argparse
import logging
import os
from typing import Literal, Optional

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
from argutils import parse_limit
from data import CalibrationConfig, CalibrationParams, get_processed_data


def plot_marker_errors(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    config_file: str = "config.json",
    calibration_file: str = "calibration.json",
    correct: bool = True,
    skip_frames: bool = True,
    time_unit: Literal["s", "frames"] = "s",
    time_limit: Optional[tuple[float, float]] = None,
    abs_error_limit: Optional[tuple[float, float]] = None,
    show_centroid: bool = True,
    show_markers: bool = True,
    show_marker_mean: bool = True,
) -> list[mpl_axes.Axes]:
    """Plot OptiTrack marker errors alongside the rigid-body centroid error.

    Two optional panels are drawn:
    - Centroid: absolute error between the OptiTrack rigid-body position and the
      gantry position (GAN.ERR[.CALIBRATED.]Abs).
    - Markers: per-marker absolute residual with respect to the rigid-body estimate
      (ERR.Abs{i}), and optionally their mean (ERR.Abs_mean).

    Args:
        gantry_file: Path to gantry CSV file.
        optitrack_file: Path to OptiTrack CSV file.
        config_file: Path to calibration configuration file.
        calibration_file: Path to calibration parameters file.
        correct: Apply the non-linear coordinate correction step.
        skip_frames: Skip the frame ranges set in the configuration file.
        time_unit: Time unit for the x-axis ('s' or 'frames').
        time_limit: Optional (min, max) x-axis limits in the chosen time unit.
        abs_error_limit: Optional (min, max) y-axis limits shared by all panels (mm).
        show_centroid: Show the centroid-vs-gantry absolute error panel.
        show_markers: Show per-marker absolute residuals in the markers panel.
        show_marker_mean: Show the mean marker residual in the markers panel.
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

    config.correction.enabled = correct
    config.skip_frames.enabled = skip_frames

    df, _, num_markers = get_processed_data(
        gantry_file,
        optitrack_file,
        config=config,
        calibration_params=calibration_params,
    )

    if not (show_centroid or show_markers or show_marker_mean):
        raise ValueError("At least one series must be enabled.")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.grid(True)

    time_data = df["time"] if time_unit == "s" else df["frame"]
    sep = ".CALIBRATED." if correct else "."

    if show_markers:
        for i in range(1, num_markers + 1):
            ax.plot(
                time_data,
                df[f"ERR.Abs{i}"],
                linewidth=0.5,
                label=f"Marker {i} error",
            )

    if show_marker_mean:
        ax.plot(
            time_data,
            df["ERR.Abs_mean"],
            "k--",
            linewidth=1.0,
            label="Marker mean error",
        )

    if show_centroid:
        ax.plot(
            time_data,
            df[f"GAN.ERR{sep}Abs"],
            "b-",
            linewidth=2,
            label="Centroid error",
        )

    ax.set_ylabel("Absolute Error (mm)")
    ax.set_xlabel(f"Time ({time_unit})")
    ax.legend()

    if time_limit is not None:
        ax.set_xlim(*time_limit)

    if abs_error_limit is not None:
        ax.set_ylim(*abs_error_limit)

    plt.tight_layout()
    plt.show()

    return [ax]


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Plot OptiTrack marker residuals and centroid error.",
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
        default="frames",
        help="Time unit for the x-axis",
    )

    parser.add_argument(
        "--time-limit",
        type=parse_limit,
        default=None,
        help="Time limit for the x-axis as 'min,max'",
    )

    parser.add_argument(
        "--abserrlim",
        type=parse_limit,
        default=None,
        help="Y-axis limit shared by all panels as 'min,max' (mm)",
    )

    parser.add_argument(
        "--centroid",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show the centroid-vs-gantry absolute error panel",
    )

    parser.add_argument(
        "--markers",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show per-marker absolute residuals",
    )

    parser.add_argument(
        "--marker-mean",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show the mean marker residual",
    )

    args = parser.parse_args()

    plot_marker_errors(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        config_file=args.config,
        calibration_file=args.calibration,
        correct=args.correct,
        skip_frames=args.skip_frames,
        time_unit=args.time_unit,
        time_limit=args.time_limit,
        abs_error_limit=args.abserrlim,
        show_centroid=args.centroid,
        show_markers=args.markers,
        show_marker_mean=args.marker_mean,
    )


if __name__ == "__main__":
    main()
