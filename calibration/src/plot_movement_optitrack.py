import argparse
from typing import Optional, cast

import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d

from data import load_optitrack_data
from argutils import parse_limit
from multipoint_player import MultiPointPlayer

from coordinates_utils import TransformRotateCenter


def plot_movement_optitrack(
    optitrack_file: str,
    trail_after_samples: int = 0,
    trail_before_samples: int = 2000,
    xlim: Optional[tuple[float, float]] = None,
    ylim: Optional[tuple[float, float]] = None,
    zlim: Optional[tuple[float, float]] = None,
) -> plt.Axes:
    """Plot Optitrack movement data in 3D.

    Args:
        filename: Path to the Optitrack CSV file
        trail_after_samples: Number of previous samples to show after the current frame
        trail_before_samples: Number of previous samples to show before the current frame
        xlim: Optional tuple of (min, max) for the x-axis
        ylim: Optional tuple of (min, max) for the y-axis
        zlim: Optional tuple of (min, max) for the z-axis
    """
    df, num_markers = load_optitrack_data(optitrack_file)

    # Set the time relative to the start time
    df["time"] = df["time"] - df["time"].iloc[0]

    # Create the figure and 3D axes
    plt.figure(figsize=(10, 8))
    ax = cast(axes3d.Axes3D, plt.subplot(projection="3d"))
    ax.set_proj_type("ortho")

    # Set axis labels
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # Set axis limits
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_zlim(zlim)

    # Create parameters for the MultiPointPlayer
    point_cols = [("RB.X", "RB.Y", "RB.Z")]
    points_styles = [{"color": "k", "marker": "x", "markersize": 5}]

    marker_cols = [
        [(f"M.X{i}", f"M.Y{i}", f"M.Z{i}") for i in range(1, num_markers + 1)],
        [(f"RB.X{i}", f"RB.Y{i}", f"RB.Z{i}") for i in range(1, num_markers + 1)],
    ]
    marker_styles = [
        {
            "color": "b",
            "linestyle": "None",
            "fillstyle": "none",
            "marker": "o",
            "markeredgewidth": 0.75,
            "markersize": 5,
        },
        {
            "color": "r",
            "linestyle": "None",
            "marker": ".",
            "markeredgewidth": 0.75,
            "markersize": 3,
        },
    ]

    trail_cols = [("RB.X", "RB.Y", "RB.Z")]
    trail_styles = [{"color": "b", "linestyle": "-", "alpha": 0.25}]

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
        blit=True,
        cache_frame_data=True,
        save_count=1000,
    )

    # Print control instructions
    print(anim.get_help_text())

    plt.tight_layout()
    plt.show()

    return ax


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot Optitrack movement",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--data",
        help="Path to the CSV file with the optitrack movement data",
        type=str,
        default="take_optitrack.csv",
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

    default_axis_limits = {
        "x": (-2500, 2500),
        "y": (-2500, 2500),
        "z": (1200, 2000),
    }

    for axis in ["x", "y", "z"]:
        parser.add_argument(
            f"--{axis}lim",
            help=f"{axis.upper()} axis limits in format 'min,max'",
            type=parse_limit,
            default=default_axis_limits[axis],
        )

    args = parser.parse_args()

    plot_movement_optitrack(
        optitrack_file=args.data,
        trail_after_samples=args.trail_after,
        trail_before_samples=args.trail_before,
        xlim=args.xlim,
        ylim=args.ylim,
        zlim=args.zlim,
    )
