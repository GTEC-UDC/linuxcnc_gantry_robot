import argparse
import logging
from typing import Any

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from argutils import parse_limit
from data import CalibrationConfig, CalibrationParams, get_processed_data
from matplotlib.ticker import MultipleLocator

DEFAULT_STYLE = {"alpha": 0.25, "s": 2, "lw": 0}
DEFAULT_FIT_STYLE = {"color": "r", "linestyle": "--", "alpha": 0.8}


def plot_errors_scatter(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    config_file: str = "config.json",
    calibration_file: str = "calibration.json",
    correct: bool = True,
    skip_samples: bool = True,
    ylim_x: tuple[float, float] | None = None,
    ylim_y: tuple[float, float] | None = None,
    ylim_z: tuple[float, float] | None = None,
    plot_fit: bool = True,
    color_cross: bool = False,
    color_map: dict[str, str] | None = None,
    xtick_step_x: float | None = None,
    xtick_step_y: float | None = None,
    xtick_step_z: float | None = None,
    cmap: str = "viridis",
    save: str | None = None,
    dpi: int = 200,
    figsize: tuple[float, float] = (10.0, 6.0),
    style: dict[str, Any] | None = None,
    fit_style: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, list[mpl_axes.Axes]]:
    """
    Plot pairwise scatter plots between gantry position and positioning errors.
    """
    style = DEFAULT_STYLE if style is None else style
    fit_style = DEFAULT_FIT_STYLE if fit_style is None else fit_style

    sep = ".CALIBRATED." if correct else "."
    errors = [f"GAN.ERR{sep}X", f"GAN.ERR{sep}Y", f"GAN.ERR{sep}Z"]
    positions = [f"GAN{sep}X", f"GAN{sep}Y", f"GAN{sep}Z"]
    axes = []

    # Per-row vertical limits, one per error component (None = autoscale)
    ylim_map = {"X": ylim_x, "Y": ylim_y, "Z": ylim_z}

    # Per-axis horizontal tick spacing, keyed by the position letter shown on
    # the horizontal axis (None = automatic). The same spacing is reused on the
    # colorbar, which always encodes an in-plane (X or Y) axis.
    xtick_step_map = {"X": xtick_step_x, "Y": xtick_step_y, "Z": xtick_step_z}

    # In-plane cross axis used to color each position column (the other
    # in-plane axis for the X/Y columns; Y for the short vertical Z column)
    if color_map is None:
        color_map = {"X": "Y", "Y": "X", "Z": "Y"}

    # In-plane workspace range, shared by the X/Y position axes and by the
    # color scale (the cross axis used for coloring is always in-plane).
    # Fixing the color range keeps the colorbar ticks symmetric and makes a
    # given position map to the same color across all columns.
    in_plane_min, in_plane_max = 0.0, 5200.0

    with open(config_file, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(calibration_file, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    # Override the skip frames parameter
    config.correction.skip_samples.enabled = skip_samples
    config.correction.reject_samples.enabled = skip_samples

    df, _, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        config=config,
        calibration_params=calibration_params,
    )

    fig = plt.figure(
        constrained_layout=True,
        figsize=figsize,
    )

    col_axes: dict[int, list[mpl_axes.Axes]] = {i: [] for i in range(len(positions))}
    col_mappable: dict[int, Any] = {}

    for i, pos in enumerate(positions):
        color_letter = color_map[pos[-1]]
        color_col = f"GAN{sep}{color_letter}"

        for j, err in enumerate(errors):
            ax = plt.subplot(3, 3, 1 + i + j * 3)
            axes.append(ax)
            col_axes[i].append(ax)

            # Rasterize only the dense point cloud; axes, grid, labels,
            # legend and the fit line stay vectorial when saving to PDF/SVG
            if color_cross:
                col_mappable[i] = ax.scatter(
                    df[pos],
                    df[err],
                    c=df[color_col],
                    cmap=cmap,
                    vmin=in_plane_min,
                    vmax=in_plane_max,
                    rasterized=True,
                    **style,
                )
            else:
                ax.scatter(df[pos], df[err], rasterized=True, **style)
            ax.grid(True)
            ax.set_xlabel(f"{pos[-1]} (mm)")
            ax.set_ylabel(f"Error {err[-1]} (mm)")
            ax.set_title(f"Error {err[-1]} over {pos[-1]}")
            ax.set_ylim(ylim_map[err[-1]])

            # Add fit line
            if plot_fit and (mask := df.loc[:, [pos, err]].notna().all(axis=1)).any():
                x = df.loc[mask, pos].to_numpy(np.float64)
                y = df.loc[mask, err].to_numpy(np.float64)

                if pos[-1] in ["X", "Y"]:
                    legend_str = "Quadratic fit"
                    z = np.polyfit(x, y, 2)
                    x = np.linspace(in_plane_min, in_plane_max, 100)
                    ax.set_xlim(in_plane_min, in_plane_max)
                else:
                    legend_str = "Linear fit"
                    z = np.polyfit(x, y, 1)
                    x = np.linspace(-1100, 0, 100)
                    ax.set_xlim(-1100, 0)

                p = np.poly1d(z)
                ax.plot(x, p(x), label=legend_str, **fit_style)
                ax.legend()

            if (step := xtick_step_map[pos[-1]]) is not None:
                ax.xaxis.set_major_locator(MultipleLocator(step))

    # One colorbar per column, labeled with the cross axis it encodes
    if color_cross:
        for i, pos in enumerate(positions):
            color_letter = color_map[pos[-1]]
            cbar = fig.colorbar(
                col_mappable[i],
                ax=col_axes[i],
                location="bottom",
                aspect=30,
                pad=0.02,
                label=f"{color_letter} (mm)",
            )
            # Horizontal colorbar: ticks live on its x-axis
            if (step := xtick_step_map[color_letter]) is not None:
                cbar.ax.xaxis.set_major_locator(MultipleLocator(step))

    if save is not None:
        plt.savefig(save, dpi=dpi, bbox_inches="tight")
    else:
        plt.show()
    return df, axes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

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
        "--skip-samples",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the sample exclusions of the configuration file",
    )

    parser.add_argument(
        "--plot-fit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Plot fitted lines",
    )

    parser.add_argument(
        "--ylim-x",
        type=parse_limit,
        help="Y-axis limit for the error X row as 'min,max' (mm)",
    )

    parser.add_argument(
        "--ylim-y",
        type=parse_limit,
        help="Y-axis limit for the error Y row as 'min,max' (mm)",
    )

    parser.add_argument(
        "--ylim-z",
        type=parse_limit,
        help="Y-axis limit for the error Z row as 'min,max' (mm)",
    )

    parser.add_argument(
        "--xtick-step-x",
        type=float,
        default=None,
        help="Horizontal tick spacing where X is on the axis/colorbar (mm)",
    )

    parser.add_argument(
        "--xtick-step-y",
        type=float,
        default=None,
        help="Horizontal tick spacing where Y is on the axis/colorbar (mm)",
    )

    parser.add_argument(
        "--xtick-step-z",
        type=float,
        default=None,
        help="Horizontal tick spacing where Z is on the axis (mm)",
    )

    parser.add_argument(
        "--color-cross",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Color each column by the position of an in-plane cross axis",
    )

    parser.add_argument(
        "--cmap",
        type=str,
        default="viridis",
        help="Colormap used when --color-cross is enabled",
    )

    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save the figure to this path instead of showing it",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Resolution of the rasterized point cloud when saving to PDF/SVG",
    )

    parser.add_argument(
        "--figsize",
        type=parse_limit,
        default=(10.0, 6.0),
        help="Figure size in inches as 'width,height'",
    )

    parser.add_argument(
        "--font",
        type=str,
        default=None,
        help="Override the font family (e.g. 'STIX Two Text')",
    )

    parser.add_argument(
        "--fontsize",
        type=float,
        default=None,
        help="Override the base font size in points",
    )

    args = parser.parse_args()

    scatter_style = (
        {"alpha": 0.25, "s": 2, "lw": 0}
        if not args.color_cross
        else {"alpha": 1, "s": 1.5, "lw": 0}
    )

    if args.font is not None:
        plt.rcParams["font.family"] = args.font
    if args.fontsize is not None:
        plt.rcParams["font.size"] = args.fontsize

    # Create scatter plots of position errors
    df, _ = plot_errors_scatter(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        config_file=args.config,
        calibration_file=args.calibration,
        correct=args.correct,
        skip_samples=args.skip_samples,
        ylim_x=args.ylim_x,
        ylim_y=args.ylim_y,
        ylim_z=args.ylim_z,
        plot_fit=args.plot_fit,
        color_cross=args.color_cross,
        xtick_step_x=args.xtick_step_x,
        xtick_step_y=args.xtick_step_y,
        xtick_step_z=args.xtick_step_z,
        cmap=args.cmap,
        save=args.save,
        dpi=args.dpi,
        figsize=args.figsize,
        style=scatter_style,
    )
