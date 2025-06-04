import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import cast

import numpy as np
import numpy.typing as npt
import pandas as pd


def coord_mse(
    df: pd.DataFrame,
    df_other: pd.DataFrame,
    df_cols: list[str] = ["x", "y", "z"],
    df_other_cols: list[str] = ["x", "y", "z"],
    time_col: str = "time",
) -> float:
    """Calculate the mean squared error of the coordinates of two dataframes."""
    assert (
        len(df_cols) == len(df_other_cols) == 3
    ), "df_cols and df_other_cols must have 3 elements"

    df_time, df_x, df_y, df_z = (
        df[time_col],
        df[df_cols[0]],
        df[df_cols[1]],
        df[df_cols[2]],
    )

    df_o_time, df_o_x, df_o_y, df_o_z = (
        df_other[time_col],
        df_other[df_other_cols[0]],
        df_other[df_other_cols[1]],
        df_other[df_other_cols[2]],
    )

    df_o_interp_x = np.interp(df_time, df_o_time, df_o_x, left=np.nan, right=np.nan)
    df_o_interp_y = np.interp(df_time, df_o_time, df_o_y, left=np.nan, right=np.nan)
    df_o_interp_z = np.interp(df_time, df_o_time, df_o_z, left=np.nan, right=np.nan)

    sq = (
        (df_x - df_o_interp_x) ** 2
        + (df_y - df_o_interp_y) ** 2
        + (df_z - df_o_interp_z) ** 2
    )

    return cast(float, np.nanmean(np.sqrt(sq)))


def coord_shift_xyz(
    df: pd.DataFrame,
    x_shift: float = 0,
    y_shift: float = 0,
    z_shift: float = 0,
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """Shift by x, y, z the coordinates of a dataframe."""
    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"

    df_shifted = df.copy()

    df_shifted[x_cols] += x_shift
    df_shifted[y_cols] += y_shift
    df_shifted[z_cols] += z_shift

    return df_shifted


def coord_rotate(
    df: pd.DataFrame,
    axis: str,
    angle: float,
    center: tuple[float, float, float] = (0, 0, 0),
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """Rotate by axis the coordinates of a dataframe by a given angle."""

    assert len(center) == 3, "center must have 3 elements: x, y, z"

    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"

    df_rotated = df.copy()
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    xc, yc, zc = center

    x, y, z = (
        (df[x_cols] - xc).to_numpy(),
        (df[y_cols] - yc).to_numpy(),
        (df[z_cols] - zc).to_numpy(),
    )

    if axis == "x":
        df_rotated[y_cols] = y * cos_a - z * sin_a + yc
        df_rotated[z_cols] = y * sin_a + z * cos_a + zc
    elif axis == "y":
        df_rotated[x_cols] = x * cos_a - z * sin_a + xc
        df_rotated[z_cols] = x * sin_a + z * cos_a + zc
    elif axis == "z":
        df_rotated[x_cols] = x * cos_a - y * sin_a + xc
        df_rotated[y_cols] = x * sin_a + y * cos_a + yc
    else:
        raise ValueError(f"Invalid axis: {axis}")

    return df_rotated


def coord_rotate_seq(
    df: pd.DataFrame,
    angles: list[tuple[str, float]],
    center: tuple[float, float, float] = (0, 0, 0),
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """Perform a sequence of rotations on the coordinates of a dataframe."""

    assert len(center) == 3, "center must have 3 elements: x, y, z"

    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"

    df_rotated = df.copy()

    for axis, angle in angles:
        df_rotated = coord_rotate(
            df_rotated, axis, angle, center, x_cols, y_cols, z_cols
        )

    return df_rotated


def coord_shift_t(
    df: pd.DataFrame,
    t_shift: float,
    time_col: str = "time",
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """Shift by time the coordinates of a dataframe."""
    if t_shift == 0.0:
        return df

    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"

    time = df[time_col]
    time_shifted = time - t_shift

    df_shifted = df.copy()
    for col in itertools.chain(x_cols, y_cols, z_cols):
        df_shifted[col] = np.interp(
            time_shifted, time, df[col], left=np.nan, right=np.nan
        )

    return df_shifted


def coord_matrix_transform(
    df: pd.DataFrame,
    matrix: npt.NDArray[np.float64],
    array: npt.NDArray[np.float64],
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """Transform the coordinates of a dataframe with a transformation matrix."""
    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"
    assert matrix.shape == (3, 3), "matrix must be a 3x3 matrix"
    assert len(array) == 3, "array must have 3 elements"

    df_tr = df.copy()

    for x, y, z in zip(x_cols, y_cols, z_cols):
        data = df_tr[[x, y, z]]
        df_tr[[x, y, z]] = data @ matrix + array

    return df_tr


def coord_matrix_transform2(
    df: pd.DataFrame,
    matrix1: npt.NDArray[np.float64],
    matrix2: npt.NDArray[np.float64],
    array: npt.NDArray[np.float64],
    x_cols: list[str] = ["x"],
    y_cols: list[str] = ["y"],
    z_cols: list[str] = ["z"],
) -> pd.DataFrame:
    """
    Transform the coordinates of a dataframe with first and second order
    transformation matrices.
    """
    assert (
        len(x_cols) == len(y_cols) == len(z_cols)
    ), "x_cols, y_cols, and z_cols must have the same length"
    assert matrix1.shape == (3, 3), "matrix1 must be a 3x3 matrix"
    assert matrix2.shape == (3, 3), "matrix2 must be a 3x3 matrix"
    assert len(array) == 3, "array must have 3 elements"

    df_tr = df.copy()

    for x, y, z in zip(x_cols, y_cols, z_cols):
        data = df_tr[[x, y, z]]
        df_tr[[x, y, z]] = data @ matrix1 + data**2 @ matrix2 + array

    return df_tr


@dataclass
class Transform(ABC):
    pass

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        pass


@dataclass
class TransformShiftT(Transform):
    t_shift: float = 0.0
    time_col: str = "time"
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return coord_shift_t(
            df, self.t_shift, self.time_col, self.x_cols, self.y_cols, self.z_cols
        )


@dataclass
class TransformShiftXYZ(Transform):
    x_shift: float = 0.0
    y_shift: float = 0.0
    z_shift: float = 0.0
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return coord_shift_xyz(
            df,
            self.x_shift,
            self.y_shift,
            self.z_shift,
            self.x_cols,
            self.y_cols,
            self.z_cols,
        )


@dataclass
class TransformRotate(Transform):
    axis: str = "x"
    angle: float = 0.0
    center: tuple[float, float, float] = (0, 0, 0)
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return coord_rotate(
            df,
            self.axis,
            self.angle,
            self.center,
            self.x_cols,
            self.y_cols,
            self.z_cols,
        )


@dataclass
class TransformRotateCenter(Transform):
    axis: str = "x"
    angle: float = 0.0
    center_cols: list[str] = field(default_factory=lambda: ["x", "y", "z"])
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        center = tuple(df[self.center_cols].mean())
        return coord_rotate(
            df, self.axis, self.angle, center, self.x_cols, self.y_cols, self.z_cols
        )


@dataclass
class TransformMatrix(Transform):
    matrix: npt.NDArray[np.float64]
    array: npt.NDArray[np.float64]
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return coord_matrix_transform(
            df, self.matrix, self.array, self.x_cols, self.y_cols, self.z_cols
        )


@dataclass
class TransformMatrix2(Transform):
    matrix1: npt.NDArray[np.float64]
    matrix2: npt.NDArray[np.float64]
    array: npt.NDArray[np.float64]
    x_cols: list[str] = field(default_factory=lambda: ["x"])
    y_cols: list[str] = field(default_factory=lambda: ["y"])
    z_cols: list[str] = field(default_factory=lambda: ["z"])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return coord_matrix_transform2(
            df,
            self.matrix1,
            self.matrix2,
            self.array,
            self.x_cols,
            self.y_cols,
            self.z_cols,
        )


def coord_transform(df: pd.DataFrame, transform: list[Transform]) -> pd.DataFrame:
    """Apply a sequence of transformations to the coordinates of a dataframe."""
    for t in transform:
        df = t.apply(df)

    return df
