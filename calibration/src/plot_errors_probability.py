# Plot the errors between the rigid body markers and the raw markers
import argparse
import logging

import matplotlib.axes as mpl_axes
import matplotlib.pyplot as plt
import numpy as np
from argutils import parse_limit
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
    plot_fit: bool = False,
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
    fig = plt.figure(figsize=(8, 6), constrained_layout=True)

    ax_x_err = fig.add_subplot(2, 2, 1)
    ax_y_err = fig.add_subplot(2, 2, 2)
    ax_z_err = fig.add_subplot(2, 2, 3)
    ax_abs_err = fig.add_subplot(2, 2, 4)

    hist_params = {
        "density": True,
        "histtype": "step",
        "cumulative": cumulative,
        "bins": bins,
    }

    for ax, name in zip(
        [ax_x_err, ax_y_err, ax_z_err, ax_abs_err], ["X", "Y", "Z", "Abs"]
    ):
        # Enable grid for all subplots
        ax.grid(True)

        # Get data and remove NaN values
        data = df[f"GAN.ERR.{name}"].dropna()
        data_calibrated = df[f"GAN.ERR.CALIBRATED.{name}"].dropna()

        # Plot error probabilities (using the filtered data)
        ax.hist(data, label="Original", **hist_params)
        ax.hist(data_calibrated, label="Calibrated", **hist_params)

        if plot_fit and name != "Abs":
            # Fit normal distributions for X, Y, Z
            mu_orig, std_orig = stats.norm.fit(data)
            mu_cal, std_cal = stats.norm.fit(data_calibrated)

            # Generate points for plotting the fitted distributions
            x = np.linspace(xyz_limits[0], xyz_limits[1], 100)

            label_orig = f"Original N fit\nμ={mu_orig:.2f}\nσ={std_orig:.2f}"
            label_cal = f"Calibrated N fit\nμ={mu_cal:.2f}\nσ={std_cal:.2f}"

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

            label_orig = f"Original R fit\nν={b_orig:.2f}\nσ={scale_orig:.2f}"
            label_cal = f"Calibrated R fit\nν={b_cal:.2f}\nσ={scale_cal:.2f}"

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

        ax.legend()
        ax.set_title(f"{name} Error")
        ax_x_err.set_ylabel(
            "Probability Density" if not cumulative else "Cumulative Probability"
        )
        ax.set_xlabel("Error (mm)")
        ax.set_xlim(abs_limits if name == "Abs" else xyz_limits)

    plt.tight_layout()
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
        )
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

    args = parser.parse_args()

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
        plot_fit=args.plot_fit,
    )
