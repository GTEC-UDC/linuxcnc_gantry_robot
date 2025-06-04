import argparse
from typing import Optional, cast

import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d

from argutils import parse_limit
from data import load_gantry_data
from point_player import PointPlayer


def plot_movement_gantry(
    gantry_file: str,
    trail_after_samples: int = 0,
    trail_before_samples: int = 2000,
    xlim: Optional[tuple[float, float]] = None,
    ylim: Optional[tuple[float, float]] = None,
    zlim: Optional[tuple[float, float]] = None,
) -> plt.Axes:
    df = load_gantry_data(gantry_file)

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

    # Create animation
    anim = PointPlayer(
        ax,
        df,
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
        description="Plot gantry movement",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--data",
        help="Path to the CSV file with the gantry movement data",
        type=str,
        default="take_gantry.csv",
    )

    parser.add_argument(
        "--trail-before",
        help="Number of previous samples to show before the current frame",
        type=int,
        default=2000,
    )

    parser.add_argument(
        "--trail-after",
        help="Number of future samples to show after the current frame",
        type=int,
        default=0,
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

    plot_movement_gantry(
        gantry_file=args.data,
        trail_after_samples=args.trail_after,
        trail_before_samples=args.trail_before,
        xlim=args.xlim,
        ylim=args.ylim,
        zlim=args.zlim,
    )
