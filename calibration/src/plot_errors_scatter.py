import argparse
from typing import Any, Optional, cast

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from argutils import parse_limit
from data import CalibrationConfig, CalibrationParams, get_processed_data


def plot_errors_scatter(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    config_file: str = "config.json",
    calibration_file: str = "calibration.json",
    correct: bool = True,
    skip_frames: bool = True,
    ylim: Optional[tuple[float, float]] = None,
    plot_fit: bool = True,
    style: dict[str, Any] = {"alpha": 0.25, "s": 2, "lw": 0},
    fit_style: dict[str, Any] = {"color": "r", "linestyle": "--", "alpha": 0.8},
) -> tuple[pd.DataFrame, list[mpl_axes.Axes]]:
    """
    Plot pairwise scatter plots between gantry position and positioning errors.
    """
    sep = ".CALIBRATED." if correct else "."
    errors = [f"GAN.ERR{sep}X", f"GAN.ERR{sep}Y", f"GAN.ERR{sep}Z"]
    positions = [f"GAN{sep}X", f"GAN{sep}Y", f"GAN{sep}Z"]
    axes = []

    with open(config_file, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(calibration_file, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    # Override the skip frames parameter
    config.skip_frames.enabled = skip_frames

    df, _, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        config=config,
        calibration_params=calibration_params,
    )

    plt.figure(
        constrained_layout=True,
        figsize=(10, 6),
    )

    for i, pos in enumerate(positions):
        for j, err in enumerate(errors):
            ax = plt.subplot(3, 3, 1 + i + j * 3)
            axes.append(ax)

            ax.scatter(df[pos], df[err], **style)
            ax.grid(True)
            ax.set_xlabel(pos[-1])
            ax.set_ylabel(f"Error {err[-1]}")
            ax.set_title(f"Error {err[-1]} over {pos[-1]}")
            ax.set_ylim(ylim)

            # Add fit line
            if plot_fit and (mask := df.loc[:, [pos, err]].notna().all(axis=1)).any():
                x = df.loc[mask, pos].to_numpy(np.float64)
                y = df.loc[mask, err].to_numpy(np.float64)

                if pos[-1] in ["X", "Y"]:
                    legend_str = "Quadratic fit"
                    z = np.polyfit(x, y, 2)
                    x = np.linspace(0, 5200, 100)
                    ax.set_xlim(0, 5200)
                else:
                    legend_str = "Linear fit"
                    z = np.polyfit(x, y, 1)
                    x = np.linspace(-1100, 0, 100)
                    ax.set_xlim(-1100, 0)

                p = np.poly1d(z)
                ax.plot(x, p(x), label=legend_str, **fit_style)
                ax.legend()

    plt.show()
    return df, axes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze gantry errors from Optitrack and Gantry data",
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
        "--plot-fit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plot fitted lines",
    )

    parser.add_argument(
        "--ylim",
        type=parse_limit,
        help="Y-axis limit for position plot as 'min,max' (mm)",
    )

    args = parser.parse_args()

    # Create scatter plots of position errors
    df, _ = plot_errors_scatter(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        config_file=args.config,
        calibration_file=args.calibration,
        correct=args.correct,
        skip_frames=args.skip_frames,
        ylim=args.ylim,
        plot_fit=args.plot_fit,
    )

    # Print statistical summary
    print("\nStatistical Summary of Errors:")
    print(df[["GAN.ERR.X", "GAN.ERR.Y", "GAN.ERR.Z", "GAN.ERR.Abs"]].describe())

    # Calculate and print R-squared values
    positions = ["GAN.X", "GAN.Y", "GAN.Z"]
    errors = ["GAN.ERR.X", "GAN.ERR.Y", "GAN.ERR.Z"]
    print("\nR-squared values for linear fits:")
    for pos in positions:
        for err in errors:
            if (mask := df.loc[:, [pos, err]].notna().all(axis=1)).any():
                correlation = cast(float, df.loc[mask, [pos, err]].corr().iloc[0, 1])
                r_squared = correlation**2
                print(f"{pos} vs {err}: {r_squared:.4f}")
