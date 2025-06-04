# Plot the errors between the rigid body markers and the raw markers
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from argutils import parse_limit
from data import get_processed_data, load_bad_frames


def plot_errors_probability(
    gantry_file: str = "take_gantry.csv",
    optitrack_file: str = "take_optitrack.csv",
    alignment_params_file: str = "alignment_params.npy",
    calibration_params_file: str = "calibration_params.npy",
    bad_frames_file: str = "bad_frames.json",
    remove_bad_frames: bool = False,
    cumulative: bool = True,
    bins: int = 200,
    xyz_limits: tuple[float, float] = (-15, 15),
    abs_limits: tuple[float, float] = (0, 20),
) -> list[plt.Axes]:

    bad_frames = None
    if remove_bad_frames:
        bad_frames = load_bad_frames(bad_frames_file)

    # Get the processed data
    df, _ = get_processed_data(
        gantry_file,
        optitrack_file,
        alignment_params_filename=alignment_params_file,
        calibration_params_filename=calibration_params_file,
        bad_frames=bad_frames,
        calibrate=True,
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

        if name != "Abs":
            # Fit normal distributions for X, Y, Z
            mu_orig, std_orig = stats.norm.fit(data)
            mu_cal, std_cal = stats.norm.fit(data_calibrated)
            
            # Generate points for plotting the fitted distributions
            x = np.linspace(xyz_limits[0], xyz_limits[1], 100)
            pdf_orig = stats.norm.pdf(x, mu_orig, std_orig)
            pdf_cal = stats.norm.pdf(x, mu_cal, std_cal)
            
            if not cumulative:
                ax.plot(x, pdf_orig, 'r--', 
                       label=f'Original N fit\nμ={mu_orig:.2f}\nσ={std_orig:.2f}')
                ax.plot(x, pdf_cal, 'g--', 
                       label=f'Calibrated N fit\nμ={mu_cal:.2f}\nσ={std_cal:.2f}')
            else:
                cdf_orig = stats.norm.cdf(x, mu_orig, std_orig)
                cdf_cal = stats.norm.cdf(x, mu_cal, std_cal)
                ax.plot(x, cdf_orig, 'r--', 
                       label=f'Original N fit\nμ={mu_orig:.2f}\nσ={std_orig:.2f}')
                ax.plot(x, cdf_cal, 'g--', 
                       label=f'Calibrated N fit\nμ={mu_cal:.2f}\nσ={std_cal:.2f}')
        else:
            # Fit Rice distributions for Abs
            s_orig, loc_orig, scale_orig = stats.rice.fit(data, loc=0)
            s_cal, loc_cal, scale_cal = stats.rice.fit(data_calibrated, loc=0)
            
            # Generate points for plotting the fitted distributions
            x = np.linspace(abs_limits[0], abs_limits[1], 100)
            pdf_orig = stats.rice.pdf(x, s_orig, loc=loc_orig, scale=scale_orig)
            pdf_cal = stats.rice.pdf(x, s_cal, loc=loc_cal, scale=scale_cal)
            
            if not cumulative:
                ax.plot(x, pdf_orig, 'r--', 
                       label=f'Original R fit\nμ={s_orig:.2f}\nσ={scale_orig:.2f}')
                ax.plot(x, pdf_cal, 'g--', 
                       label=f'Calibrated R fit\nμ={s_cal:.2f}\nσ={scale_cal:.2f}')
            else:
                cdf_orig = stats.rice.cdf(x, s_orig, loc=loc_orig, scale=scale_orig)
                cdf_cal = stats.rice.cdf(x, s_cal, loc=loc_cal, scale=scale_cal)
                ax.plot(x, cdf_orig, 'r--', 
                       label=f'Original R fit\nμ={s_orig:.2f}\nσ={scale_orig:.2f}')
                ax.plot(x, cdf_cal, 'g--', 
                       label=f'Calibrated R fit\nμ={s_cal:.2f}\nσ={scale_cal:.2f}')

        ax.legend()
        ax.set_title(f"{name} Error")
        ax_x_err.set_ylabel(
            "Probability Density" if not cumulative else "Cumulative Probability"
        )
        ax.set_xlabel("Error (mm)")

        # Set axis limits based on the error type
        if name == "Abs":
            ax.set_xlim(abs_limits)
        else:
            ax.set_xlim(xyz_limits)

    plt.tight_layout()
    plt.show()

    return [ax_x_err, ax_y_err, ax_z_err, ax_abs_err]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Analyze gantry errors from Optitrack and gantry data",
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
        help="Path to the CSV file with the Optitrack movement data",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to CSV file with the gantry movement data",
    )

    parser.add_argument(
        "--alignment",
        type=str,
        default="alignment_params.npy",
        help="Path to alignment parameters file",
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
        alignment_params_file=args.alignment,
        calibration_params_file=args.calibration,
        bad_frames_file=args.bad_frames,
        remove_bad_frames=args.remove_bad_frames,
        cumulative=args.cumulative,
        bins=args.bins,
        xyz_limits=args.xyzlim,
        abs_limits=args.abslim,
    )
