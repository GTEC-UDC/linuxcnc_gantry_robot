import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
import scipy as scp
import scipy.spatial.transform as scp_tr
from pydantic import BaseModel, Field, PositiveInt

logger = logging.getLogger(__name__)

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool]


def load_gantry_data(filename: str | Path) -> pd.DataFrame:
    """Load gantry position data from a CSV file.

    Args:
        filename (str | Path): Path to the CSV file containing gantry data.

    Returns:
        pd.DataFrame: DataFrame containing the gantry position data.
    """
    return cast(pd.DataFrame, pd.read_csv(filename))


def load_optitrack_metadata(filename: str | Path) -> dict[str, Any]:
    """Load and parse OptiTrack metadata from a CSV file.

    This function reads the first line of an OptiTrack CSV file and parses the metadata
    information, including capture frame rate, export frame rate, start frame, total
    frames, and capture start time.

    Args:
        filename (str | Path): Path to the OptiTrack CSV file.

    Returns:
        dict[str, Any]: Dictionary containing parsed metadata with the following keys:
            - Take Name
            - Capture Frame Rate (float)
            - Export Frame Rate (float)
            - Capture Start Frame (int)
            - Total Frames in Take (int)
            - Total Exported Frames (int)
            - Capture Start Time (datetime)
    """
    with open(filename, "r") as f:
        line = f.readline().strip()

    items = line.split(",")
    metadata: dict[str, Any] = {k: v for k, v in zip(items[::2], items[1::2]) if k}
    take_name = metadata["Take Name"]

    # Convert numeric data
    metadata["Capture Frame Rate"] = float(metadata["Capture Frame Rate"])
    metadata["Export Frame Rate"] = float(metadata["Export Frame Rate"])
    metadata["Capture Start Frame"] = int(metadata["Capture Start Frame"])
    metadata["Total Frames in Take"] = int(metadata["Total Frames in Take"])
    metadata["Total Exported Frames"] = int(metadata["Total Exported Frames"])

    # Convert capture start date and time
    # The date is in the format "2025-02-21 12.00.00.000"
    # Note that the time is given in 12-hour format but no AM/PM is given
    # Although the system time is set correctly, the capture start time
    # reported in the data seems to be off by a few seconds, so it cannot
    # be used directly to get the actual start time
    capture_date_str = (
        metadata["Capture Start Time"].strip()
        + " "
        + ("PM" if take_name.endswith("PM") else "AM")
    )
    date_format = "%Y-%m-%d %I.%M.%S.%f %p"
    metadata["Capture Start Time"] = datetime.strptime(capture_date_str, date_format)  # noqa: DTZ007

    return metadata


def load_optitrack_data(
    filename: str | Path, rigid_body_name: str | None = None
) -> tuple[pd.DataFrame, int]:
    """Load and process OptiTrack motion capture data from a CSV file.

    This function loads OptiTrack data, processes marker positions, calculates errors
    between raw and rigid body markers, and computes various statistics.

    Args:
        filename (str | Path): Path to the OptiTrack CSV file.
        rigid_body_name (Optional[str], optional): Name of the rigid body to process.
            If None, uses the first rigid body found in the data. Defaults to None.

    Returns:
        tuple[pd.DataFrame, int]: A tuple containing:
            - DataFrame with processed OptiTrack data including marker positions,
              rigid body positions, errors, and centroids
            - Number of markers detected

    Raises:
        ValueError: If the number of rigid body markers doesn't match the number of
            raw markers, or if an unknown column type is encountered.
    """
    df: pd.DataFrame = pd.read_csv(filename, header=[1, 2, 4, 5])

    # Get the columns we want to keep and create new names
    df_cols = list(df.columns[:2])
    df_col_names = ["frame", "time"]
    num_rb_m = 0
    num_m = 0

    if rigid_body_name is None:
        rigid_body_name = cast(str, df.columns[2][1])
        logger.info("Found rigid body name: %s", rigid_body_name)

    for col in df.columns[2:]:
        if col[2] != "Position":
            continue

        if col[1] == rigid_body_name:
            df_cols.append(col)
            df_col_names.append(f"RB.{col[3]}")
        elif match := re.match(rf"^{re.escape(rigid_body_name)}:Marker(\d+)$", col[1]):
            df_cols.append(col)
            n = int(match.group(1))

            if col[0] == "Marker":
                df_col_names.append(f"M.{col[3]}{n}")
                num_m = max(num_m, n)
            elif col[0] == "Rigid Body Marker":
                df_col_names.append(f"RB.{col[3]}{n}")
                num_rb_m = max(num_rb_m, n)
            else:
                raise ValueError(f"Unknown column type: {col[0]}")

    if num_rb_m != num_m:
        raise ValueError(
            f"Number of rigid body markers ({num_rb_m}) does not match "
            f"the number of markers ({num_m})"
        )

    # Create a new dataframe with the columns we want to keep
    df = df.loc[:, df_cols]
    df.columns = pd.Index(df_col_names)

    # Calculate errors for the markers
    for i in range(1, num_m + 1):
        for coord in ["X", "Y", "Z"]:
            rb_coords = df[f"RB.{coord}{i}"]
            raw_coords = df[f"M.{coord}{i}"]
            df[f"ERR.{coord}{i}"] = raw_coords - rb_coords

        df[f"ERR.Abs{i}"] = np.sqrt(
            df[f"ERR.X{i}"] ** 2 + df[f"ERR.Y{i}"] ** 2 + df[f"ERR.Z{i}"] ** 2
        )

    # Calculate the mean errors across all markers
    for coord in ["X", "Y", "Z"]:
        # Calculate mean error for each coordinate
        error_cols = [f"ERR.{coord}{i}" for i in range(1, num_m + 1)]
        df[f"ERR.{coord}_mean"] = df[error_cols].mean(axis=1)

    # Calculate mean absolute error
    abs_error_cols = [f"ERR.Abs{i}" for i in range(1, num_m + 1)]
    df["ERR.Abs_mean"] = df[abs_error_cols].mean(axis=1)

    # Find the frames where no raw markers were detected
    raw_markers_na = df[[f"M.X{i}" for i in range(1, num_m + 1)]].isna().all(axis=1)

    # Calculate the centroid of the markers
    for coord in ["X", "Y", "Z"]:
        cols = [f"M.{coord}{i}" for i in range(1, num_m + 1)]
        df_coords = df[cols]

        # Interpolate the OptiTrack data to fill the missing values
        df_coords = df_coords.interpolate(
            method="linear", axis=0, limit_area="inside", inplace=False
        )

        df[f"M.{coord}_centroid"] = df_coords.mean(axis=1)

    # Set to NA the coordinates where no raw markers were detected
    m_centroid_cols = [f"M.{coord}_centroid" for coord in ["X", "Y", "Z"]]
    df.loc[raw_markers_na, m_centroid_cols] = np.nan

    rb_cols = ["RB.X", "RB.Y", "RB.Z"] + [
        f"RB.{coord}{i}" for i in range(1, num_m + 1) for coord in ["X", "Y", "Z"]
    ]
    df.loc[raw_markers_na, rb_cols] = np.nan

    return df, num_m


Vector3 = tuple[float, float, float]
Matrix3 = tuple[Vector3, Vector3, Vector3]

# Highest power of each coordinate (x, y, z) in the correction model
Degree = tuple[PositiveInt, PositiveInt, PositiveInt]
DEFAULT_DEGREE: Degree = (2, 2, 1)


class CorrectionModel(ABC):
    """A model that corrects gantry positions."""

    @abstractmethod
    def apply(self, pos: FloatArray) -> FloatArray:
        """Apply the model to an (N, 3) array of positions, or to a single one."""


class PolynomialCorrection(BaseModel, CorrectionModel):
    """Polynomial correction model of the gantry positions.

    The corrected position is

        pos_corrected = c + A[0] @ pos + A[1] @ pos**2 + ... + A[n-1] @ pos**n

    where pos is a position (x, y, z), pos**k is its elementwise power, c is a
    constant offset, and A holds one 3x3 matrix per power. The degree n of the
    model is the number of matrices. A power of a coordinate that the model does
    not use has a zero column in its matrix.
    """

    c: Vector3
    A: list[Matrix3] = Field(min_length=1)

    @property
    def degree(self) -> int:
        return len(self.A)

    def apply(self, pos: FloatArray) -> FloatArray:
        out = np.zeros_like(pos, dtype=float) + np.array(self.c)
        power = np.ones_like(pos, dtype=float)
        for matrix in self.A:
            power = power * pos
            out = out + power @ np.array(matrix).T
        return out


def correction_terms(degree: Degree = DEFAULT_DEGREE) -> list[tuple[int, int]]:
    """Terms of the correction model besides the constant, as (power, axis) pairs.

    The terms are ordered by power, and by axis within each power. The default
    degree is (2, 2, 1).

    Examples:
        With degree (2, 2, 1) the terms are x, y, z, x**2 and y**2, and the
        returned value is
        [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]

        With degree (3, 3, 1) the terms are x, y, z, x**2, y**2, x**3 and y**3,
        and the returned value is
        [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (3, 0), (3, 1)]
    """
    return [
        (power, axis)
        for power in range(1, max(degree) + 1)
        for axis in range(3)
        if power <= degree[axis]
    ]


def design_matrix(
    gantry_samples: FloatArray, degree: Degree = DEFAULT_DEGREE
) -> FloatArray:
    """Design matrix of the correction model for a set of gantry positions.

    The matrix has one row per position and one column per term of the model.
    The columns are the terms of ``correction_terms``, in the same order and
    evaluated at each position, followed by a column of ones for the constant.

    Args:
        gantry_samples (FloatArray): Gantry positions, shape (N, 3).
        degree (Degree): Highest power of x, y and z in the model.

    Returns:
        FloatArray: Design matrix, shape (N, T + 1), with T the number of terms
            of ``correction_terms``.

    Examples:
        With degree (2, 2, 1) the columns are [x, y, z, x**2, y**2, 1].
        For samples [[2, 3, 5], [10, 20, 30]] the result is
        [[ 2,  3,  5,   4,   9, 1],
         [10, 20, 30, 100, 400, 1]]
    """
    cols = [
        gantry_samples[:, axis] ** power for power, axis in correction_terms(degree)
    ]
    return np.column_stack(cols + [np.ones(len(gantry_samples))])


def correction_from_coef(
    coef: FloatArray, degree: Degree, scale: FloatArray
) -> PolynomialCorrection:
    """Parameters of the correction model from the coefficients of a fit.

    ``coef`` has one row per column of the design matrix, built from the gantry
    positions divided by ``scale``. The scaling is undone here, so the parameters
    apply to the positions as they are.

    Args:
        coef (FloatArray): Coefficients of the fit, shape (T + 1, 3), with T the
            number of terms of ``correction_terms``. Each row holds the
            coefficients of one term for x, y and z, and the last row is c.
        degree (Degree): Highest power of x, y and z in the model.
        scale (FloatArray): Scale of each coordinate, shape (3,).

    Returns:
        PolynomialCorrection: Correction model with the parameters of the fit.
    """
    mat_a = np.zeros((max(degree), 3, 3))
    for row, (k, axis) in zip(coef, correction_terms(degree)):
        mat_a[k - 1, :, axis] = row / scale[axis] ** k
    return PolynomialCorrection.model_validate(
        {"c": coef[-1].tolist(), "A": mat_a.tolist()}
    )


def correction_scale(gantry: FloatArray) -> FloatArray:
    """Scale of each coordinate that brings the gantry positions to [-1, 1].

    The correction model is fitted on the scaled positions. In millimeters the
    columns of the design matrix span too many orders of magnitude (x**3 reaches
    1e11 against the column of ones), which makes the matrix ill-conditioned.
    ``numpy.linalg.lstsq`` treats as zero the singular values below the value
    specified in the `rcond` parameter. The default value for `rcond` (when None
    is specified) is the machine precision times the number of samples.

    Args:
        gantry (FloatArray): Gantry positions, shape (N, 3). NaN are ignored.

    Returns:
        FloatArray: Largest absolute value of each coordinate, shape (3,), or 1
            for a coordinate that is always zero.
    """
    scale = np.nanmax(np.abs(gantry), axis=0)
    scale[scale == 0] = 1.0
    return scale


def fit_correction(
    gantry_samples: FloatArray,
    optitrack_samples: FloatArray,
    degree: Degree = DEFAULT_DEGREE,
) -> PolynomialCorrection:
    """Least squares fit of the correction model that maps gantry onto optitrack.

    Args:
        gantry_samples (FloatArray): Gantry positions, shape (N, 3).
        optitrack_samples (FloatArray): OptiTrack positions, shape (N, 3), paired
            row by row with the gantry ones.
        degree (Degree): Highest power of x, y and z in the model.

    Returns:
        PolynomialCorrection: Fitted correction model.
    """
    valid = ~np.isnan(gantry_samples).any(axis=1) & ~np.isnan(optitrack_samples).any(
        axis=1
    )

    gantry_samples = gantry_samples[valid]
    optitrack_samples = optitrack_samples[valid]

    scale = correction_scale(gantry_samples)
    design = design_matrix(gantry_samples / scale, degree)
    coef, _, _, _ = np.linalg.lstsq(design, optitrack_samples, rcond=None)
    return correction_from_coef(coef, degree, scale)


def reject_samples(
    gantry_samples: FloatArray,
    optitrack_samples: FloatArray,
    time: FloatArray,
    sigma: float = 5.0,
    margin_s: float = 0.25,
    iterations: int = 2,
    degree: Degree = DEFAULT_DEGREE,
) -> BoolArray:
    """Samples of the correction fit to keep, found by iterated outlier rejection.

    Fits the model, measures the 3D residual, and rejects every sample farther than
    ``sigma`` robust standard deviations from its median. The fit is then repeated
    on what is left. Each rejected sample takes with it the ``margin_s`` seconds on
    either side of it, which covers the entry and exit ramps of a tracking dropout,
    already corrupted while still below the threshold.

    The spread is measured with the median absolute deviation
    (https://en.wikipedia.org/wiki/Median_absolute_deviation) rather than the
    standard deviation, because the standard deviation is itself inflated by the
    very samples we are looking for, which raises the threshold until they pass it.
    The 1.4826 factor makes the MAD match the standard deviation for Gaussian data,
    so ``sigma`` keeps its usual meaning.

    The samples must be free of NaN and ordered in time.

    Args:
        gantry_samples (FloatArray): Gantry positions, shape (N, 3).
        optitrack_samples (FloatArray): OptiTrack positions, shape (N, 3), paired
            row by row with the gantry ones.
        time (FloatArray): Time of each sample in seconds, shape (N,).
        sigma (float): Rejection threshold, in robust standard deviations.
        margin_s (float): Time rejected on either side of a rejected sample, in
            seconds.
        iterations (int): Number of rounds of fit and rejection, at least one.
        degree (Degree): Highest power of x, y and z in the model.

    Returns:
        BoolArray: Mask of the samples to keep, shape (N,).
    """
    keep = np.ones(len(gantry_samples), dtype=bool)

    for _ in range(max(iterations, 1)):
        correction = fit_correction(
            gantry_samples[keep], optitrack_samples[keep], degree
        )
        residual = np.linalg.norm(
            correction.apply(gantry_samples) - optitrack_samples, axis=1
        )
        median = np.median(residual)
        spread = np.median(np.abs(residual - median)) * 1.4826
        rejected = residual >= median + sigma * spread

        if margin_s > 0 and rejected.any():
            # Each rejected sample widens into the interval of samples
            # within `margin_s` seconds of it, and the mask is the union
            # of those intervals. Every interval contributes one +1 and
            # one -1 to the edge count, so the running sum gives how
            # many of them cover each sample.
            start = np.searchsorted(time, time[rejected] - margin_s, side="left")
            end = np.searchsorted(time, time[rejected] + margin_s, side="right")
            edges = np.zeros(len(time) + 1, dtype=int)
            np.add.at(edges, start, 1)
            np.add.at(edges, end, -1)
            rejected = np.cumsum(edges[:-1]) > 0

        keep = ~rejected

    return keep


def interp_columns(t: FloatArray, t_src: FloatArray, values: FloatArray) -> FloatArray:
    """Resample the columns of ``values``, taken at ``t_src``, onto the times ``t``.

    ``values`` has one row per sample of ``t_src`` and any number of columns,
    each interpolated independently. Times outside the range covered by
    ``t_src`` are returned as NaN.

    Args:
        t (FloatArray): Times to resample onto, shape (M,) or (M, 1).
        t_src (FloatArray): Times of the samples, increasing, shape (N,) or (N, 1).
        values (FloatArray): Samples, shape (N, K).

    Returns:
        FloatArray: Resampled values, shape (M, K).
    """
    t = t.flatten()
    t_src = t_src.flatten()

    return np.column_stack(
        [
            np.interp(t, t_src, values[:, i], left=np.nan, right=np.nan)
            for i in range(values.shape[1])
        ]
    )


class MinimizeOptions(BaseModel):
    # Options for scipy.optimize.minimize_scalar.
    # Method should be one of the supported by scipy.optimize.minimize_scalar
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html
    method: Literal["brent", "golden"] | None = "brent"
    tolerance: float | None = 1e-9
    display: bool = True


class CalibrationAlignmentConfig(BaseModel):
    enabled: bool = True
    init_time_offset: float | None = None
    minimize_options: MinimizeOptions = Field(default_factory=MinimizeOptions)


class RejectSamplesConfig(BaseModel):
    # Automatic rejection of the samples. See reject_samples().
    enabled: bool = True
    sigma: float = 5.0
    margin_s: float = 0.25
    iterations: int = 2


class SkipSamplesConfig(BaseModel):
    # Sample ranges to exclude from the correction fit.
    enabled: bool = False
    ranges: list[tuple[int, int]] = Field(default_factory=list)


class CalibrationCorrectionConfig(BaseModel):
    enabled: bool = True
    # Highest power of x, y and z in the correction model. See PolynomialCorrection.
    degree: Degree = DEFAULT_DEGREE
    reject_samples: RejectSamplesConfig = Field(default_factory=RejectSamplesConfig)
    skip_samples: SkipSamplesConfig = Field(default_factory=SkipSamplesConfig)


class CalibrationConfig(BaseModel):
    alignment: CalibrationAlignmentConfig = Field(
        default_factory=CalibrationAlignmentConfig
    )
    correction: CalibrationCorrectionConfig = Field(
        default_factory=CalibrationCorrectionConfig
    )


class AlignmentTransform(BaseModel):
    """Alignment of the OptiTrack positions with the gantry positions.

    The aligned position at time t is

        pos_aligned(t) = R @ pos(t - time_offset) + translation

    where pos is a position (x, y, z) and R is the rotation matrix of ``rotation``.

    Attributes:
        time_offset: Time shift in seconds.
        rotation: Rotation angles (rx, ry, rz) in radians about the fixed x, y and
            z axes, applied in that order (R = Rz @ Ry @ Rx).
        translation: Translation (tx, ty, tz) in mm.
    """

    time_offset: float
    rotation: Vector3
    translation: Vector3

    @classmethod
    def from_vector(cls, x: npt.ArrayLike) -> "AlignmentTransform":
        """Build alignment from vector (dt, rx, ry, rz, tx, ty, tz)."""
        dt, rx, ry, rz, tx, ty, tz = np.asarray(x, dtype=float).tolist()
        return cls(time_offset=dt, rotation=(rx, ry, rz), translation=(tx, ty, tz))

    def to_vector(self) -> FloatArray:
        """Alignment as vector (dt, rx, ry, rz, tx, ty, tz)."""
        return np.array([self.time_offset, *self.rotation, *self.translation])

    def apply(
        self,
        time: FloatArray,
        samples: FloatArray,
    ) -> FloatArray:
        """Align positions.

        The alignment shifts the time base, rotates, and translates.

        Args:
            time (FloatArray): Time of each sample in seconds, shape (N,) or (N, 1).
            samples (FloatArray): Positions, shape (N, 3).

        Returns:
            FloatArray: Aligned positions, shape (N, 3). The samples shifted outside
                the time range are NaN.
        """
        ret = interp_columns(time - self.time_offset, time, samples)
        ret = scp_tr.Rotation.from_euler("xyz", self.rotation).apply(ret)
        ret += np.asarray(self.translation)
        return ret


class CalibrationParams(BaseModel):
    alignment: AlignmentTransform | None = None
    correction: PolynomialCorrection | None = None


def load_correction(filename: str | Path) -> PolynomialCorrection:
    """Load the parameters of the correction model from a file."""
    with open(filename, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    if calibration_params.correction is None:
        raise ValueError(f"No correction parameters in {filename}")

    return calibration_params.correction


def samples_mse(a: FloatArray, b: FloatArray) -> float:
    """Mean squared distance between two sets of positions paired row by row.

    Args:
        a (FloatArray): Positions, shape (N, 3).
        b (FloatArray): Positions, shape (N, 3).

    Returns:
        float: Mean of the squared distances, ignoring the pairs with NaN.
    """
    return float(np.nanmean(np.sum((a - b) ** 2, axis=1)))


def samples_mean_distance(a: FloatArray, b: FloatArray) -> float:
    """Mean distance between two sets of positions paired row by row.

    Args:
        a (FloatArray): Positions, shape (N, 3).
        b (FloatArray): Positions, shape (N, 3).

    Returns:
        float: Mean of the distances, ignoring the pairs with NaN.
    """
    return float(np.nanmean(np.sqrt(np.sum((a - b) ** 2, axis=1))))


def fit_rigid_transform(
    source: FloatArray, target: FloatArray
) -> tuple[FloatArray, FloatArray]:
    """Find the rotation and the translation that best move ``source`` to ``target``.

    Both arrays have one x, y, z row per point. The result minimizes the squared
    distance between ``source @ rotation.T + translation`` and ``target``
    (Kabsch algorithm).
    """
    valid = ~np.isnan(source).any(axis=1) & ~np.isnan(target).any(axis=1)
    source = source[valid, :]
    target = target[valid, :]

    source_center = source.mean(axis=0)
    target_center = target.mean(axis=0)

    best_rotation, _ = scp_tr.Rotation.align_vectors(
        target - target_center, source - source_center
    )

    rotation = best_rotation.as_matrix()
    return rotation, target_center - rotation @ source_center


def fit_alignment(
    time: FloatArray,
    gantry_samples: FloatArray,
    optitrack_samples: FloatArray,
    config: CalibrationAlignmentConfig | None = None,
) -> AlignmentTransform:
    """Fit the alignment of the OptiTrack positions with the gantry positions.

    The alignment shifts the OptiTrack positions in time, rotates them and
    translates them (see ``AlignmentTransform``). For a given time shift, the
    rotation and the translation that minimize the mean squared error are found
    with the Kabsch algorithm (see ``fit_rigid_transform``). The time shift is
    found with a numerical minimization of that error, starting at
    ``config.init_time_offset``. This minimization is local, so the initial time
    shift must be close to the real one.

    Args:
        time (FloatArray): Time of each sample in seconds, shape (N,) or (N, 1).
        gantry_samples (FloatArray): Gantry positions, shape (N, 3).
        optitrack_samples (FloatArray): OptiTrack positions, shape (N, 3), paired
            row by row with the gantry ones. The pairs with NaN are ignored.
        config (CalibrationAlignmentConfig | None): Settings of the fit. None
            uses the default ones.

    Returns:
        AlignmentTransform: Fitted alignment.
    """
    g_xyz, o_xyz = gantry_samples, optitrack_samples
    config = config or CalibrationAlignmentConfig()
    t0 = config.init_time_offset or 0

    def align_fn(time_offset: float) -> float:
        optitrack_shift = interp_columns(time - time_offset, time, o_xyz)
        rotation, translation = fit_rigid_transform(optitrack_shift, g_xyz)
        return samples_mse(g_xyz, optitrack_shift @ rotation.T + translation)

    logger.info("Aligning OptiTrack data with gantry data...")

    res = scp.optimize.minimize_scalar(
        fun=align_fn,
        bracket=(t0 - 0.5, t0 + 0.5),
        tol=config.minimize_options.tolerance,
        options={"disp": 1 if config.minimize_options.display else 0},
        method=config.minimize_options.method,
    )

    if not res.success:
        logger.warning("The alignment fit did not converge: %s", res.message)

    time_offset = float(res.x)
    optitrack_shift = interp_columns(time - time_offset, time, optitrack_samples)
    rotation, translation = fit_rigid_transform(optitrack_shift, gantry_samples)

    alignment = AlignmentTransform(
        time_offset=time_offset,
        rotation=scp_tr.Rotation.from_matrix(rotation).as_euler("xyz").tolist(),
        translation=translation.tolist(),
    )

    logger.info("Alignment completed. Parameters: %s", alignment)

    o_xyz_corrected = optitrack_shift @ rotation.T + translation
    mean_dist_err = samples_mean_distance(g_xyz, o_xyz_corrected)
    mean_sq_err = samples_mse(g_xyz, o_xyz_corrected)

    logger.info("Alignment mean distance error: %f", mean_dist_err)
    logger.info("Alignment mean square error: %f", mean_sq_err)

    return alignment


def get_processed_data(
    gantry_filename: str | Path,
    optitrack_filename: str | Path,
    config: CalibrationConfig | None = None,
    calibration_params: CalibrationParams | None = None,
) -> tuple[pd.DataFrame, CalibrationParams, int]:
    """Align and calibrate the gantry and OptiTrack data.

    This function loads gantry and OptiTrack data, aligns them temporally and
    spatially, handles bad frames, and optionally performs calibration, i.e.,
    corrects misalignments between the gantry and the OptiTrack system.

    Args:
        gantry_filename (str | Path): Path to the gantry data CSV file.
        optitrack_filename (str | Path): Path to the OptiTrack data CSV file.
        config (CalibrationConfig, optional): Configuration for the data
            processing. If None an empty CalibrationConfig object is created.
            Defaults to None.
        calibration_params (CalibrationParams, optional): Calibration parameters.
            If None an empty CalibrationParams object is created. Defaults to None.

    Returns:
        tuple[pd.DataFrame, CalibrationParams, int]: A tuple containing:
            - DataFrame with the processed and aligned data
            - Calibration parameters
            - Number of markers detected
    """
    config = config or CalibrationConfig()
    calibration_params = calibration_params or CalibrationParams()

    # -------------------------------------------------------------------------
    # Load the Gantry and the OptiTrack data
    # -------------------------------------------------------------------------

    df_o, num_markers = load_optitrack_data(optitrack_filename)
    df_g = load_gantry_data(gantry_filename)

    metadata_o = load_optitrack_metadata(optitrack_filename)

    # -------------------------------------------------------------------------
    # Combine the data
    # -------------------------------------------------------------------------

    capture_start_time = metadata_o["Capture Start Time"].timestamp()

    df = df_o.copy()
    gan = interp_columns(
        df_o["time"].to_numpy(),
        df_g["time"].to_numpy() - capture_start_time,
        df_g[["x", "y", "z"]].to_numpy(),
    )
    df["GAN.X"], df["GAN.Y"], df["GAN.Z"] = gan[:, 0], gan[:, 1], gan[:, 2]

    # -------------------------------------------------------------------------
    # Align the OptiTrack data with the gantry data
    # -------------------------------------------------------------------------

    alignment: AlignmentTransform | None = None
    if config.alignment.enabled and calibration_params.alignment is not None:
        alignment = calibration_params.alignment
    elif config.alignment.enabled:
        time = df.loc[:, ["time"]].to_numpy()
        g_xyz = df.loc[:, ["GAN.X", "GAN.Y", "GAN.Z"]].to_numpy()  # Gantry data
        o_xyz = df.loc[:, ["RB.X", "RB.Y", "RB.Z"]].to_numpy()  # OptiTrack data

        alignment = fit_alignment(time, g_xyz, o_xyz, config.alignment)

    if alignment is not None:
        # Transform all the OptiTrack coordinates in the dataframe
        time = df.loc[:, "time"].to_numpy()
        for x_col in [col for col in df.columns if col.startswith(("M.X", "RB.X"))]:
            cols = [x_col.replace(".X", f".{axis}", 1) for axis in "XYZ"]
            df[cols] = alignment.apply(time, df[cols].to_numpy())

    # -------------------------------------------------------------------------
    # Skip samples
    #
    # This step removes hand-picked ranges of samples by setting their coordinate
    # values to NaN, which keeps them out of the correction fit and out of
    # everything derived from it. The ranges are indices of this dataframe, which
    # holds one row per sample. It is done after alignment so we don't remove
    # non-aligned data points.
    # -------------------------------------------------------------------------

    coord_cols = [col for col in df.columns if col not in ("time", "frame")]

    if config.correction.skip_samples.enabled:
        for start, end in config.correction.skip_samples.ranges:
            logger.info("Skipping samples %d to %d", start, end)
            df.loc[start:end, coord_cols] = np.nan

    # -------------------------------------------------------------------------
    # Reject samples
    #
    # Reject samples automatically. OptiTrack samples with a large error are
    # found through the residual of the correction model and are removed from
    # the record.
    # -------------------------------------------------------------------------

    if config.correction.enabled and config.correction.reject_samples.enabled:
        g_xyz = df[["GAN.X", "GAN.Y", "GAN.Z"]].to_numpy()
        o_xyz = df[["RB.X", "RB.Y", "RB.Z"]].to_numpy()
        time = df["time"].to_numpy()
        valid = ~np.isnan(g_xyz).any(axis=1) & ~np.isnan(o_xyz).any(axis=1)
        valid = cast(np.typing.NDArray[np.bool], valid)

        reject_opts = config.correction.reject_samples
        keep = reject_samples(
            g_xyz[valid],
            o_xyz[valid],
            time[valid],
            sigma=reject_opts.sigma,
            margin_s=reject_opts.margin_s,
            iterations=reject_opts.iterations,
            degree=config.correction.degree,
        )

        logger.info(
            "Rejected %d of %d samples (%.2f %%)",
            int((~keep).sum()),
            len(keep),
            100 * (~keep).mean(),
        )

        df.loc[df.index[valid][~keep], coord_cols] = np.nan

    # -------------------------------------------------------------------------
    # Correct the gantry positions
    #
    # The correction model maps the gantry positions onto the aligned OptiTrack
    # positions:
    #
    #    pos_optitrack = c + A_1 @ pos_gantry + ... + A_n @ pos_gantry**n
    #
    # where the powers are element-wise, c is a vector and A_1, ..., A_n are 3x3
    # matrices (see ``PolynomialCorrection``). Each coordinate enters with the
    # powers up to its entry in ``config.correction.degree``.
    # -------------------------------------------------------------------------

    correction: PolynomialCorrection | None = None
    degree = config.correction.degree

    if config.correction.enabled and calibration_params.correction is not None:
        correction = calibration_params.correction

        if correction.degree != max(degree):
            logger.warning(
                "The correction parameters are of degree %d, but the degree of the "
                "configuration is %s",
                correction.degree,
                degree,
            )
    elif config.correction.enabled:
        g_xyz = df.loc[:, ["GAN.X", "GAN.Y", "GAN.Z"]].to_numpy()  # Gantry data
        o_xyz = df.loc[:, ["RB.X", "RB.Y", "RB.Z"]].to_numpy()  # OptiTrack data

        logger.info("Fitting correction model for gantry data...")
        correction = fit_correction(g_xyz, o_xyz, degree)

        g_xyz_corrected = correction.apply(g_xyz)
        mean_dist_err = samples_mean_distance(o_xyz, g_xyz_corrected)
        mean_sq_err = samples_mse(o_xyz, g_xyz_corrected)

        logger.info("Correction completed. Parameters: %s", correction)
        logger.info("Correction mean distance error: %f", mean_dist_err)
        logger.info("Correction mean square error: %f", mean_sq_err)

    if correction is not None:
        df_correct: pd.DataFrame = df.loc[:, ["GAN.X", "GAN.Y", "GAN.Z"]]
        df_correct.columns = pd.Index(["x", "y", "z"])
        df_correct[["x", "y", "z"]] = correction.apply(
            df_correct[["x", "y", "z"]].to_numpy()
        )

        # Add final calibrated coordinates to the dataframe
        df["GAN.CALIBRATED.X"] = df_correct["x"]
        df["GAN.CALIBRATED.Y"] = df_correct["y"]
        df["GAN.CALIBRATED.Z"] = df_correct["z"]
    else:
        # Add final calibrated coordinates with nan values
        df["GAN.CALIBRATED.X"] = np.nan
        df["GAN.CALIBRATED.Y"] = np.nan
        df["GAN.CALIBRATED.Z"] = np.nan

    # -----------------------------------------------------------------------------
    # Calculate Gantry errors
    # -----------------------------------------------------------------------------

    for coord_sep in [".", ".CALIBRATED."]:
        df[f"GAN.ERR{coord_sep}X"] = df["RB.X"] - df[f"GAN{coord_sep}X"]
        df[f"GAN.ERR{coord_sep}Y"] = df["RB.Y"] - df[f"GAN{coord_sep}Y"]
        df[f"GAN.ERR{coord_sep}Z"] = df["RB.Z"] - df[f"GAN{coord_sep}Z"]

        df[f"GAN.ERR{coord_sep}Abs"] = np.sqrt(
            df[f"GAN.ERR{coord_sep}X"] ** 2
            + df[f"GAN.ERR{coord_sep}Y"] ** 2
            + df[f"GAN.ERR{coord_sep}Z"] ** 2
        )

    # -------------------------------------------------------------------------
    # Create the CalibrationParams object to return
    # -------------------------------------------------------------------------

    calibration_params = CalibrationParams(
        alignment=alignment,
        correction=correction,
    )

    # -------------------------------------------------------------------------
    # Return the processed data
    # -------------------------------------------------------------------------

    return df, calibration_params, num_markers
