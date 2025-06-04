import argparse
from typing import Optional, cast

import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d
import numpy as np

from argutils import parse_limit
from data import get_processed_data, load_bad_frames
from multipoint_player import MultiPointPlayer


def plot_movement(
    gantry_file: str,
    optitrack_file: str,
    alignment_params_file: str,
    calibration_params_file: str,
    trail_after_samples: int = 0,
    trail_before_samples: int = 2000,
    error_after_samples: int = 2000,
    error_before_samples: int = 2000,
    remove_bad_frames: bool = False,
    bad_frames_file: str = "bad_frames.json",
    show_calibrated: bool = True,
    xlim: Optional[tuple[float, float]] = None,
    ylim: Optional[tuple[float, float]] = None,
    zlim: Optional[tuple[float, float]] = None,
) -> plt.Axes:
    """Plot gantry and Optitrack movement data in 3D.

    Args:
        gantry_file: Path to the gantry CSV file
        optitrack_file: Path to the Optitrack CSV file
        alignment_params_file: Path to the alignment parameters file
        calibration_params_file: Path to the calibration parameters file
        trail_after_samples: Number of previous samples to show for the trails
        trail_before_samples: Number of previous samples to show for the trails
        error_after_samples: Number of previous samples to show for the errors
        error_before_samples: Number of previous samples to show for the errors
        remove_bad_frames: Whether to remove bad frames from the data
        bad_frames_file: Path to the bad frames file
        show_calibrated: Whether to show the gantry position after calibration
        xlim: Optional tuple of (min, max) for the x-axis
        ylim: Optional tuple of (min, max) for the y-axis
        zlim: Optional tuple of (min, max) for the z-axis
    """
    bad_frames = None
    if remove_bad_frames:
        bad_frames = load_bad_frames(bad_frames_file)

    # Load and process the data
    df, num_markers = get_processed_data(
        gantry_file,
        optitrack_file,
        alignment_params_file,
        calibration_params_file,
        bad_frames=bad_frames,
        calibrate=True,
    )

    # Set the time relative to the start time
    df["time"] = df["time"] - df["time"].iloc[0]

    # Create the figure and subplots
    fig = plt.figure(figsize=(15, 8))
    gs = fig.add_gridspec(
        4, 2, width_ratios=[2, 1]
    )  # 4 rows, 2 columns with main plot wider

    # Main 3D plot
    ax = cast(axes3d.Axes3D, fig.add_subplot(gs[:, 0], projection="3d"))
    ax.set_proj_type("ortho")

    # Error subplots
    error_axes = []
    error_lines_aligned = []  # Position aligned but not calibrated
    error_lines_calibrated = []  # Position aligned and calibrated
    time_lines = []

    for i in range(4):
        ax_error = fig.add_subplot(gs[i, 1])
        ax_error.set_ylabel(f"{['X', 'Y', 'Z', 'Abs'][i]} Error (mm)")
        ax_error.grid(True)
        ax_error.autoscale(enable=True, axis="y")
        ax_error.set_xlim(-error_before_samples / 60, error_after_samples / 60)
        if i < 3:
            ax_error.set_ylim(-15, 15)
        else:
            ax_error.set_ylim(0, 30)
        error_axes.append(ax_error)

        line_aligned = ax_error.plot(
            [], [], "b-", alpha=0.5, linewidth=0.5, label="Uncalibrated"
        )[0]
        line_calibrated = ax_error.plot(
            [], [], "r-", alpha=0.5, linewidth=0.5, label="Calibrated"
        )[0]
        time_line = ax_error.axvline(x=0, color="r", linestyle="--", alpha=0.5)

        error_lines_aligned.append(line_aligned)
        error_lines_calibrated.append(line_calibrated)
        time_lines.append(time_line)
        ax_error.legend()

    error_axes[-1].set_xlabel("Time (s)")

    # Set axis labels and limits
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_zlim(zlim)

    # Create parameters for the MultiPointPlayer
    sep = ".CALIBRATED." if show_calibrated else "."
    point_cols = [
        (f"GAN{sep}X", f"GAN{sep}Y", f"GAN{sep}Z"),  # Gantry position
        ("RB.X", "RB.Y", "RB.Z"),  # Rigid body center
    ]

    points_styles = [
        {
            "color": "k",
            "marker": "x",
            "linestyle": "None",
            "markersize": 7,
            "label": "Gantry",
        },  # Gantry point style
        {
            "color": "k",
            "linestyle": "None",
            "fillstyle": "none",
            "marker": "o",
            "markeredgewidth": 0.75,
            "markersize": 6,
            "label": "Rigid body centroid",
        },  # RB center style
    ]

    marker_cols = [
        [
            (f"RB.X{i}", f"RB.Y{i}", f"RB.Z{i}") for i in range(1, num_markers + 1)
        ],  # RB markers
        [
            (f"M.X{i}", f"M.Y{i}", f"M.Z{i}") for i in range(1, num_markers + 1)
        ],  # Raw markers
    ]
    marker_styles = [
        {
            "color": "r",
            "linestyle": "None",
            "fillstyle": "none",
            "marker": "o",
            "markeredgewidth": 0.75,
            "markersize": 6,
            "label": "Rigid body markers",
        },  # RB markers style
        {
            "color": "k",
            "marker": "+",
            "linestyle": "None",
            "markeredgewidth": 0.75,
            "markersize": 5,
            "label": "Raw markers",
        },  # Raw markers style
    ]

    trail_cols = [
        (f"GAN{sep}X", f"GAN{sep}Y", f"GAN{sep}Z"),  # Gantry trail
        ("RB.X", "RB.Y", "RB.Z"),  # RB trail
    ]

    trail_styles = [
        {
            "color": "b",
            "linestyle": "-",
            "alpha": 1,
            "linewidth": 0.5,
            "label": "Gantry trail",
        },  # Gantry trail style
        {
            "color": "g",
            "linestyle": "-",
            "alpha": 1,
            "linewidth": 0.75,
            "label": "Rigid body trail",
        },  # RB trail style
    ]

    # Add text annotations for coordinates
    rb_text = ax.text2D(0.02, 0.09, "", transform=ax.transAxes)
    gan_text = ax.text2D(0.02, 0.06, "", transform=ax.transAxes)
    gan_calib_text = ax.text2D(0.02, 0.03, "", transform=ax.transAxes)

    def update_cb(frame_data):
        # Update error plots
        err_n_min = max(0, (frame_data.frame_idx - error_before_samples))
        err_n_max = min(len(df), (frame_data.frame_idx + error_after_samples))
        times = df["time"][err_n_min:err_n_max]

        for i, (error_line_aligned, error_line_calibrated) in enumerate(
            zip(error_lines_aligned, error_lines_calibrated)
        ):
            col_name = f"GAN.ERR.{['X', 'Y', 'Z', 'Abs'][i]}"
            errors = df[col_name][err_n_min:err_n_max]
            error_line_aligned.set_data(times - frame_data.frame_time, errors)

            col_name = f"GAN.ERR.CALIBRATED.{['X', 'Y', 'Z', 'Abs'][i]}"
            errors = df[col_name][err_n_min:err_n_max]
            error_line_calibrated.set_data(times - frame_data.frame_time, errors)

        # Update coordinate texts
        rb_pos = np.array(df.iloc[frame_data.frame_idx][["RB.X", "RB.Y", "RB.Z"]])
        rb_text.set_text(f"RB: ({rb_pos[0]:.2f}, {rb_pos[1]:.2f}, {rb_pos[2]:.2f})")

        gan_pos = np.array(df.iloc[frame_data.frame_idx][["GAN.X", "GAN.Y", "GAN.Z"]])
        gan_text.set_text(
            f"Gantry: ({gan_pos[0]:.2f}, {gan_pos[1]:.2f}, {gan_pos[2]:.2f})"
        )

        gan_calib_pos = np.array(
            df.iloc[frame_data.frame_idx][
                ["GAN.CALIBRATED.X", "GAN.CALIBRATED.Y", "GAN.CALIBRATED.Z"]
            ]
        )
        gan_calib_text.set_text(
            f"Gantry Calibrated: ({gan_calib_pos[0]:.2f}, "
            f"{gan_calib_pos[1]:.2f}, {gan_calib_pos[2]:.2f})"
        )

        return (
            error_lines_aligned
            + error_lines_calibrated
            + time_lines
            + [rb_text, gan_text, gan_calib_text]
        )

    # Create animation
    anim = MultiPointPlayer(
        ax,
        df,
        point_cols=point_cols,
        points_styles=points_styles,
        marker_cols=marker_cols,
        marker_styles=marker_styles,
        trail_cols=trail_cols,
        trail_styles=trail_styles,
        trail_after_samples=trail_after_samples,
        trail_before_samples=trail_before_samples,
        update_cb=update_cb,
        blit=True,
        cache_frame_data=True,
        save_count=1000,
    )

    ax.legend(loc="lower right")

    # Print control instructions
    print(anim.get_help_text())

    plt.tight_layout()
    plt.show()

    return ax


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot gantry and Optitrack movement comparison",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--gantry",
        help="Path to the CSV file with the gantry movement data",
        type=str,
        default="take_gantry.csv",
    )

    parser.add_argument(
        "--optitrack",
        help="Path to the CSV file with the Optitrack movement data",
        type=str,
        default="take_optitrack.csv",
    )

    parser.add_argument(
        "--alignment",
        help="Path to the alignment parameters file",
        type=str,
        default="alignment_params.npy",
    )

    parser.add_argument(
        "--show-calibrated",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show the gantry position after calibration",
    )

    parser.add_argument(
        "--calibration",
        help="Path to the calibration parameters file",
        type=str,
        default="calibration_params.npy",
    )

    parser.add_argument(
        "--trail-before",
        help="Number of previous samples to show before the current frame",
        type=int,
        default=2000,
    )

    parser.add_argument(
        "--trail-after",
        help="Number of previous samples to show after the current frame",
        type=int,
        default=0,
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

    default_axis_limits = {
        "x": (0, 5000),
        "y": (0, 5000),
        "z": (-1100, -500),
    }

    for axis in ["x", "y", "z"]:
        parser.add_argument(
            f"--{axis}lim",
            help=f"{axis.upper()} axis limits in format 'min,max'",
            type=parse_limit,
            default=default_axis_limits[axis],
        )

    args = parser.parse_args()

    plot_movement(
        gantry_file=args.gantry,
        optitrack_file=args.optitrack,
        alignment_params_file=args.alignment,
        calibration_params_file=args.calibration,
        trail_after_samples=args.trail_after,
        trail_before_samples=args.trail_before,
        remove_bad_frames=args.remove_bad_frames,
        bad_frames_file=args.bad_frames,
        show_calibrated=args.show_calibrated,
        xlim=args.xlim,
        ylim=args.ylim,
        zlim=args.zlim,
    )
