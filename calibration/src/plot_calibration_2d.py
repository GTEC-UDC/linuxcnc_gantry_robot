import argparse

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.widgets import Button, Slider

from data import get_calibration_matrices


def coord_transform(
    data: npt.NDArray[np.float64],
    matrix1: npt.NDArray[np.float64],
    matrix2: npt.NDArray[np.float64],
    array: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """
    Transform coordinates with first and second order transformation matrices.
    """
    return data @ matrix1 + data**2 @ matrix2 + array


class TransformationPlotter:
    def __init__(self, matrix1: np.ndarray, matrix2: np.ndarray, array: np.ndarray):
        assert matrix1.shape == (3, 3)
        assert matrix2.shape == (3, 3)
        assert array.shape == (3,)
        self.matrix1 = matrix1
        self.matrix2 = matrix2
        self.array = array

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(14, 7))
        plt.subplots_adjust(bottom=0.3)  # Make room for sliders

        # Initial values
        self.current_coord = "x"
        self.coord_indices = {"x": 0, "y": 1, "z": 2}
        self.fixed_values = {"x": 0.0, "y": 0.0, "z": -1050.0}
        self.ranges = {"x": (0, 5200), "y": (0, 5200), "z": (-1050, 0)}

        # Create coordinate selection buttons
        self.buttons = []
        self.button_axes = []
        for i, coord in enumerate(["x", "y", "z"]):
            ax = self.fig.add_axes((0.1 + i * 0.125, 0.05, 0.1, 0.05))
            button = Button(ax, f"{coord.upper()} axis")
            button.on_clicked(lambda event, c=coord: self.set_coordinate(c))
            self.buttons.append(button)
            self.button_axes.append(ax)

        # Create sliders for other coordinates
        self.sliders = {}
        self.update_sliders()

        # Create plots for left subplot (ax1)
        self.identity_line = self.ax1.plot([], [], "r-", lw=1, label="Identity line")[0]
        self.transformed_line = self.ax1.plot(
            [], [], "b--", lw=1.5, label="Transformed"
        )[0]

        # Create plot for right subplot (ax2)
        self.difference_line = self.ax2.plot([], [], "g-", lw=1.5, label="Difference")[
            0
        ]

        self.update_main_axes()
        self.update_plot()
        plt.show()

    def update_sliders(self):
        # Clear existing sliders
        for slider in self.sliders.values():
            slider.ax.remove()
        self.sliders.clear()

        # Create new sliders for the non-selected coordinates
        other_coords = [c for c in ["x", "y", "z"] if c != self.current_coord]
        for i, coord in enumerate(other_coords):
            ax = self.fig.add_axes((0.1, 0.175 - i * 0.05, 0.8, 0.03))
            slider = Slider(
                ax,
                f"{coord.upper()}",
                self.ranges[coord][0],
                self.ranges[coord][1],
                valinit=self.fixed_values[coord],
            )
            slider.on_changed(lambda val, c=coord: self.update_fixed_value(c, val))
            self.sliders[coord] = slider

    def update_main_axes(self):
        # Update left subplot
        self.ax1.set_xlim(
            self.ranges[self.current_coord][0], self.ranges[self.current_coord][1]
        )
        self.ax1.set_ylim(
            self.ranges[self.current_coord][0], self.ranges[self.current_coord][1]
        )

        # Update right subplot
        self.ax2.set_xlim(
            self.ranges[self.current_coord][0], self.ranges[self.current_coord][1]
        )
        self.ax2.set_ylim(-15, 15)

    def set_coordinate(self, coord):
        self.current_coord = coord
        self.update_sliders()
        self.update_main_axes()
        self.update_plot()

    def update_fixed_value(self, coord, value):
        self.fixed_values[coord] = value
        self.update_plot()

    def update_plot(self):
        range_min, range_max = self.ranges[self.current_coord]

        # Create matrix of coordinates
        coord_arrays = []
        for coord in ["x", "y", "z"]:
            if coord == self.current_coord:
                coord_values = np.linspace(range_min, range_max, 100)
            else:
                coord_values = np.full(100, self.fixed_values[coord])
            coord_arrays.append(coord_values)

        coords = np.vstack(coord_arrays).transpose()

        # Apply transformation
        coords_transformed = coord_transform(
            coords, self.matrix1, self.matrix2, self.array
        )

        # Get current coordinate index
        curr_idx = self.coord_indices[self.current_coord]

        # Update left subplot
        self.identity_line.set_data(
            coords[:, curr_idx],
            coords[:, curr_idx],
        )
        self.transformed_line.set_data(
            coords[:, curr_idx],
            coords_transformed[:, curr_idx],
        )

        # Update right subplot (difference plot)
        self.difference_line.set_data(
            coords[:, curr_idx],
            coords_transformed[:, curr_idx] - coords[:, curr_idx],
        )

        # Update labels and titles
        self.ax1.set_xlabel(f"Original {self.current_coord.upper()}")
        self.ax1.set_ylabel(f"Transformed {self.current_coord.upper()}")
        self.ax1.legend()
        self.ax1.grid(True)

        self.ax2.set_xlabel(f"Original {self.current_coord.upper()}")
        self.ax2.set_ylabel("Difference (transformed - original)")
        self.ax2.legend()
        self.ax2.grid(True)

        # Update title with current fixed values
        fixed_str = ", ".join(
            [
                f"{k}={v:.2f}"
                for k, v in self.fixed_values.items()
                if k != self.current_coord
            ]
        )
        self.fig.suptitle(f"Coordinate transformation\nFixed values: {fixed_str}")

        plt.draw()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot calibration parameters with 2D plots",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--calibration",
        type=str,
        default="calibration_params.npy",
        help="Path to calibration parameters file",
    )

    args = parser.parse_args()

    calibration_params = np.load(args.calibration)
    matrix1, matrix2, array = get_calibration_matrices(calibration_params)

    plotter = TransformationPlotter(matrix1, matrix2, array)
