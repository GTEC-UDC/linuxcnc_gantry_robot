# Plot the errors between the rigid body markers and the raw markers
import argparse
import logging
from typing import Optional

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
import numpy as np
from argutils import parse_limit
from matplotlib.ticker import MultipleLocator
from data import CalibrationConfig, CalibrationParams, get_processed_data
from scipy import stats


def plot_errors_probability(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    config_file: str = "config.json",
    calibration_file: str = "calibration.json",
    skip_frames: bool = True,
    cumulative: bool = True,
    bins: int = 200,
    xyz_limits: tuple[float, float] = (-15, 15),
    abs_limits: tuple[float, float] = (0, 20),
    y_limits: Optional[tuple[float, float]] = None,
    xyz_xtick_step: Optional[float] = None,
    abs_xtick_step: Optional[float] = None,
    ytick_step: Optional[float] = None,
    plot_fit: bool = False,
    linewidth: float = 1.5,
    figsize: tuple[float, float] = (8.0, 6.0),
    legend_loc: str = "outside upper center",
    save: Optional[str] = None,
    dpi: int = 200,
) -> list[mpl_axes.Axes]:
    with open(config_file, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(calibration_file, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    # Override the skip frames parameter
    config.skip_frames.enabled = skip_frames

    # Ensure the correction is enabled
    assert (
        config.correction.enabled
    ), "Correction must be enabled in the configuration file"

    # Get the processed data
    df, _, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        config=config,
        calibration_params=calibration_params,
    )

    # Create the subplots
    fig = plt.figure(figsize=figsize, constrained_layout=True)

    ax_x_err = fig.add_subplot(2, 2, 1)
    ax_y_err = fig.add_subplot(2, 2, 2)
    ax_z_err = fig.add_subplot(2, 2, 3)
    ax_abs_err = fig.add_subplot(2, 2, 4)

    # Histogram parameters for the probability density case (the cumulative case
    # uses ecdf, so bins/cumulative do not apply there)
    hist_params = {
        "density": True,
        "histtype": "step",
        "bins": bins,
        "linewidth": linewidth,
    }

    for ax, name in zip(
        [ax_x_err, ax_y_err, ax_z_err, ax_abs_err], ["X", "Y", "Z", "Abs"]
    ):
        # Enable grid for all subplots
        ax.grid(True)

        # Get data and remove NaN values
        data = df[f"GAN.ERR.{name}"].dropna()
        data_calibrated = df[f"GAN.ERR.CALIBRATED.{name}"].dropna()

        # Plot error probabilities (using the filtered data).
        if cumulative:
            ax.ecdf(data, label="Uncorrected", linewidth=linewidth)
            ax.ecdf(data_calibrated, label="Corrected", linewidth=linewidth)
        else:
            ax.hist(data, label="Uncorrected", **hist_params)
            ax.hist(data_calibrated, label="Corrected", **hist_params)

        if plot_fit and name != "Abs":
            # Fit normal distributions for X, Y, Z
            mu_orig, std_orig = stats.norm.fit(data)
            mu_cal, std_cal = stats.norm.fit(data_calibrated)

            # Generate points for plotting the fitted distributions
            x = np.linspace(xyz_limits[0], xyz_limits[1], 100)

            label_orig = f"Uncorrected N fit\nμ={mu_orig:.2f}\nσ={std_orig:.2f}"
            label_cal = f"Corrected N fit\nμ={mu_cal:.2f}\nσ={std_cal:.2f}"

            if not cumulative:
                pdf_orig = stats.norm.pdf(x, mu_orig, std_orig)
                pdf_cal = stats.norm.pdf(x, mu_cal, std_cal)

                ax.plot(x, pdf_orig, "r--", label=label_orig)
                ax.plot(x, pdf_cal, "g--", label=label_cal)
            else:
                cdf_orig = stats.norm.cdf(x, mu_orig, std_orig)
                cdf_cal = stats.norm.cdf(x, mu_cal, std_cal)

                ax.plot(x, cdf_orig, "r--", label=label_orig)
                ax.plot(x, cdf_cal, "g--", label=label_cal)
        elif plot_fit:
            # Fit Rice distributions for Abs
            b_orig, loc_orig, scale_orig = stats.rice.fit(data, floc=0)
            b_cal, loc_cal, scale_cal = stats.rice.fit(data_calibrated, floc=0)

            # Generate points for plotting the fitted distributions
            x = np.linspace(abs_limits[0], abs_limits[1], 100)

            label_orig = f"Uncorrected R fit\nν={b_orig:.2f}\nσ={scale_orig:.2f}"
            label_cal = f"Corrected R fit\nν={b_cal:.2f}\nσ={scale_cal:.2f}"

            if not cumulative:
                pdf_orig = stats.rice.pdf(x, b_orig, loc=loc_orig, scale=scale_orig)
                pdf_cal = stats.rice.pdf(x, b_cal, loc=loc_cal, scale=scale_cal)

                ax.plot(x, pdf_orig, "r--", label=label_orig)
                ax.plot(x, pdf_cal, "g--", label=label_cal)
            else:
                cdf_orig = stats.rice.cdf(x, b_orig, loc=loc_orig, scale=scale_orig)
                cdf_cal = stats.rice.cdf(x, b_cal, loc=loc_cal, scale=scale_cal)

                ax.plot(x, cdf_orig, "r--", label=label_orig)
                ax.plot(x, cdf_cal, "g--", label=label_cal)

        # With fitted curves each panel has distinct labels (its own mu/sigma)
        if plot_fit:
            ax.legend()

        ax.set_title(f"{name} Error")
        ax.set_xlabel("Error (mm)")
        ax.set_xlim(abs_limits if name == "Abs" else xyz_limits)
        if y_limits is not None:
            ax.set_ylim(y_limits)

        x_step = abs_xtick_step if name == "Abs" else xyz_xtick_step
        if x_step is not None:
            ax.xaxis.set_major_locator(MultipleLocator(x_step))
        if ytick_step is not None:
            ax.yaxis.set_major_locator(MultipleLocator(ytick_step))

        # y-label only on the left column
        if ax in (ax_x_err, ax_z_err):
            ax.set_ylabel(
                "Probability Density" if not cumulative else "Cumulative Probability"
            )

    # Single shared legend outside the axes
    if not plot_fit:
        handles, labels = ax_x_err.get_legend_handles_labels()
        fig.legend(
            handles, labels, loc=legend_loc, ncol=len(labels), borderaxespad=0.25
        )

    if save is not None:
        plt.savefig(save, dpi=dpi, bbox_inches="tight")
    else:
        plt.show()

    return [ax_x_err, ax_y_err, ax_z_err, ax_abs_err]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Analyze gantry errors from OptiTrack and gantry data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--cumulative",
        action="store_true",
        help="Plot the cumulative distribution",
    )

    parser.add_argument(
        "--bins",
        type=int,
        default=200,
        help="Number of bins for the histogram",
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
        help="Path to CSV file with the gantry movement data",
    )

    parser.add_argument(
        "--calibration",
        type=str,
        default="calibration.json",
        help="Path to calibration parameters file",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to the calibration configuration file",
    )

    parser.add_argument(
        "--skip-frames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable skipping the frames set in the configuration file",
    )

    parser.add_argument(
        "--plot-fit",
        action="store_true",
        default=False,
        help=(
            "Plot fitted normal distributions for X, Y, Z errors and "
            "Rice distributions for Abs error"
        ),
    )

    parser.add_argument(
        "--xyzlim",
        type=parse_limit,
        default=(-15, 15),
        help="X, Y, and Z plot limits (min,max) in mm",
    )

    parser.add_argument(
        "--abslim",
        type=parse_limit,
        default=(0, 20),
        help="Absolute error plot limits (min,max) in mm",
    )

    parser.add_argument(
        "--ylim",
        type=parse_limit,
        default=None,
        help="Y-axis (probability) limits (min,max), shared by all panels",
    )

    parser.add_argument(
        "--xyz-xtick-step",
        type=float,
        default=None,
        help="Spacing between x-axis ticks for the X, Y, Z error panels (mm)",
    )

    parser.add_argument(
        "--abs-xtick-step",
        type=float,
        default=None,
        help="Spacing between x-axis ticks for the absolute error panel (mm)",
    )

    parser.add_argument(
        "--ytick-step",
        type=float,
        default=None,
        help="Spacing between y-axis (probability) ticks, shared by all panels",
    )

    parser.add_argument(
        "--linewidth",
        type=float,
        default=1.5,
        help="Line width of the histogram curves",
    )

    parser.add_argument(
        "--legend-loc",
        type=str,
        default="outside upper center",
        help=(
            "Location of the shared figure legend "
            "(e.g. 'outside upper center', 'outside lower center')"
        ),
    )

    parser.add_argument(
        "--figsize",
        type=parse_limit,
        default=(8.0, 6.0),
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
        help="Resolution when saving the figure",
    )

    args = parser.parse_args()

    if args.font is not None:
        plt.rcParams["font.family"] = args.font
    if args.fontsize is not None:
        plt.rcParams["font.size"] = args.fontsize

    plot_errors_probability(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        config_file=args.config,
        calibration_file=args.calibration,
        skip_frames=args.skip_frames,
        cumulative=args.cumulative,
        bins=args.bins,
        xyz_limits=args.xyzlim,
        abs_limits=args.abslim,
        y_limits=args.ylim,
        xyz_xtick_step=args.xyz_xtick_step,
        abs_xtick_step=args.abs_xtick_step,
        ytick_step=args.ytick_step,
        plot_fit=args.plot_fit,
        linewidth=args.linewidth,
        legend_loc=args.legend_loc,
        figsize=args.figsize,
        save=args.save,
        dpi=args.dpi,
    )
