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

        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection="3d")
        plt.subplots_adjust(bottom=0.3)  # Make room for sliders

        # Initial values
        self.current_coord = "z"  # We'll plot differences in z as default
        self.coord_indices = {"x": 0, "y": 1, "z": 2}
        self.initial_values = {"x": 0.0, "y": 0.0, "z": -1050.0}
        self.fixed_value = 0.0
        self.ranges = {"x": (0, 5200), "y": (0, 5200), "z": (-1050, 0)}

        # Create coordinate selection buttons
        self.buttons = []
        self.button_axes = []
        for i, coord in enumerate(["x", "y", "z"]):
            ax = self.fig.add_axes((0.1 + i * 0.125, 0.05, 0.1, 0.05))
            button = Button(ax, f"{coord.upper()} diff")
            button.on_clicked(lambda event, c=coord: self.set_coordinate(c))
            self.buttons.append(button)
            self.button_axes.append(ax)

        # Create initial slider
        self.slider_ax = None
        self.slider = None
        self.update_slider()

        # Create surface plot
        self.surf = None
        self.colorbar = None

        # Variables for plotting the mesh grid
        self.plot_coords = None
        self.mesh_ax1 = None
        self.mesh_ax2 = None

        self.update_mesh()
        self.update_plot()
        plt.show()

    def update_slider(self):
        # Remove old slider if it exists
        if self.slider_ax is not None:
            self.slider_ax.remove()

        # Create new slider
        self.slider_ax = self.fig.add_axes((0.1, 0.15, 0.8, 0.03))
        self.slider = Slider(
            self.slider_ax,
            f"{self.current_coord.upper()}",
            self.ranges[self.current_coord][0],
            self.ranges[self.current_coord][1],
            valinit=self.initial_values[self.current_coord],
        )
        self.slider.on_changed(self.update_fixed_value)

    def update_mesh(self):
        # Determine which coordinates to use for the mesh grid
        self.plot_coords = [c for c in ["x", "y", "z"] if c != self.current_coord]
        coord1, coord2 = self.plot_coords

        # Create mesh grid
        range_ax1 = np.linspace(self.ranges[coord1][0], self.ranges[coord1][1], 10)
        range_ax2 = np.linspace(self.ranges[coord2][0], self.ranges[coord2][1], 10)
        self.mesh_ax1, self.mesh_ax2 = np.meshgrid(range_ax1, range_ax2)

    def set_coordinate(self, coord):
        self.current_coord = coord
        self.update_slider()
        self.update_mesh()
        self.update_plot()

    def update_fixed_value(self, value):
        self.fixed_value = value
        self.update_plot()

    def update_plot(self):
        coord1, coord2 = self.plot_coords

        # Get mesh grid
        mesh_ax1, mesh_ax2 = self.mesh_ax1, self.mesh_ax2

        # Create coordinate arrays
        coords = np.zeros((mesh_ax1.size, 3))
        coords[:, self.coord_indices[coord1]] = mesh_ax1.flatten()
        coords[:, self.coord_indices[coord2]] = mesh_ax2.flatten()
        coords[:, self.coord_indices[self.current_coord]] = self.fixed_value

        # Apply transformation
        coords_transformed = coord_transform(
            coords, self.matrix1, self.matrix2, self.array
        )

        # Calculate differences
        diff = (
            coords_transformed[:, self.coord_indices[self.current_coord]]
            - coords[:, self.coord_indices[self.current_coord]]
        )
        mesh_diff = diff.reshape(mesh_ax1.shape)

        # Remove existing surface plot
        if self.surf is not None:
            self.colorbar.remove()
            self.surf.remove()

        # Create new surface plot
        self.surf = self.ax.plot_surface(mesh_ax1, mesh_ax2, mesh_diff, cmap="viridis")
        self.colorbar = self.fig.colorbar(
            self.surf,
            label=f"Difference in {self.current_coord} (transformed - original)",
        )

        # Set z limits
        self.ax.set_zlim(-10, 10)

        # Set labels
        self.ax.set_xlabel(coord1.upper())
        self.ax.set_ylabel(coord2.upper())
        self.ax.set_zlabel(f"{self.current_coord.upper()} Difference")

        # Update title
        self.ax.set_title(
            f"Coordinate transformation difference\nFixed {self.current_coord}={self.fixed_value:.2f}"
        )

        plt.draw()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot calibration parameters with 3D plots",
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
