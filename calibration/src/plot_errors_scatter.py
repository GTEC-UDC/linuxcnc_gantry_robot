import argparse
from typing import Any, Optional, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from argutils import parse_limit
from data import get_processed_data, load_bad_frames


def plot_errors_scatter(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    alignment_params_file: str = "alignment_params.npy",
    calibration_params_file: str = "calibration_params.npy",
    calibrate: bool = True,
    bad_frames_file: str = "bad_frames.json",
    remove_bad_frames: bool = True,
    ylim: Optional[tuple[float, float]] = None,
    plot_fit: bool = True,
    style: dict[str, Any] = {"alpha": 0.25, "s": 2, "lw": 0},
    fit_style: dict[str, Any] = {"color": "r", "linestyle": "--", "alpha": 0.8},
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, list[plt.Axes]]:
    """
    Plot pairwise scatter plots between gantry position and positioning errors.

    Args:
        df: DataFrame containing gantry and error data
        save_path: Optional path to save the plots
    """
    sep = ".CALIBRATED." if calibrate else "."
    errors = [f"GAN.ERR{sep}X", f"GAN.ERR{sep}Y", f"GAN.ERR{sep}Z"]
    positions = [f"GAN{sep}X", f"GAN{sep}Y", f"GAN{sep}Z"]
    axes = []

    bad_frames = None
    if remove_bad_frames:
        bad_frames = load_bad_frames(bad_frames_file)

    df, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        alignment_params_file,
        calibration_params_file,
        bad_frames=bad_frames,
        calibrate=calibrate,
    )

    plt.figure(constrained_layout=True)

    for i, pos in enumerate(positions):
        for j, err in enumerate(errors):
            ax = plt.subplot(3, 3, 1 + i + j * 3)
            axes.append(ax)

            ax.scatter(df[pos], df[err], **style)
            ax.grid(True)
            ax.set_xlabel(pos)
            ax.set_ylabel(err)
            ax.set_title(f"{err} vs {pos}")
            ax.set_ylim(ylim)

            # Add fit line
            if plot_fit and (mask := df[[pos, err]].notna().all(axis=1)).any():
                x = df.loc[mask, pos]
                y = df.loc[mask, err]
                if pos[-1] in ["X", "Y"]:
                    legend_str = "Quadratic fit"
                    z = np.polyfit(x, y, 2)
                    x = np.linspace(0, 5200, 100)
                    ax.set_xlim(0, 5200)
                else:
                    legend_str = "Linear fit"
                    z = np.polyfit(x, y, 1)
                    x = np.linspace(-1050, 0, 100)
                    ax.set_xlim(-1050, 0)

                p = np.poly1d(z)
                ax.plot(x, p(x), label=legend_str, **fit_style)
                ax.legend()

    # plt.tight_layout(pad=0.1)
    if save_path:
        plt.savefig(save_path)
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
        "--alignment",
        type=str,
        default="alignment_params.npy",
        help="Path to alignment parameters file",
    )

    parser.add_argument(
        "--calibrate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Calibrate the Optitrack data",
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
        help="Path to bad frames data file",
    )

    parser.add_argument(
        "--plot-fit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plot fit line",
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
        alignment_params_file=args.alignment,
        calibration_params_file=args.calibration,
        calibrate=args.calibrate,
        bad_frames_file=args.bad_frames,
        remove_bad_frames=args.remove_bad_frames,
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
            mask = df[[pos, err]].notna().all(axis=1)
            if mask.any():
                correlation = cast(float, df.loc[mask, [pos, err]].corr().iloc[0, 1])
                r_squared = correlation**2
                print(f"{pos} vs {err}: {r_squared:.4f}")
