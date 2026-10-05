import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
import scipy as scp
from coordinates_utils import (
    TransformRotate,
    TransformShiftT,
    TransformShiftXYZ,
    coord_mean_distance,
    coord_mse,
    coord_transform,
)
from pydantic import BaseModel, Field, PositiveInt

logger = logging.getLogger(__name__)

# Center about which the rotations of the alignment are applied
ROTATION_CENTER = (0.0, 0.0, 1500.0)


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
    """A model that corrects gantry positions.

    The model in use is ``CorrectionParams``. Other models can derive from this
    class to take its place where only the corrected positions are needed, as when
    comparing alternatives to it.
    """

    @abstractmethod
    def apply(self, pos: np.ndarray) -> np.ndarray:
        """Apply the model to an (N, 3) array of positions, or to a single one."""


class CorrectionParams(BaseModel, CorrectionModel):
    # Parameters of the correction model
    #
    #   pos_corrected = c + A[0] @ pos + A[1] @ pos**2 + ... + A[n-1] @ pos**n
    #
    # where pos is a position (x, y, z), pos**k is its elementwise power, c is a
    # constant offset, and A holds one 3x3 matrix per power. The degree n of the
    # model is the number of matrices. A power of a coordinate that the model does
    # not use has a zero column in its matrix.
    c: Vector3
    A: list[Matrix3] = Field(min_length=1)

    @property
    def degree(self) -> int:
        return len(self.A)

    def apply(self, pos: np.ndarray) -> np.ndarray:
        out = np.zeros_like(pos, dtype=float) + np.array(self.c)
        power = np.ones_like(pos, dtype=float)
        for matrix in self.A:
            power = power * pos
            out = out + power @ np.array(matrix).T
        return out


def coord_align(
    x,
    df: pd.DataFrame,
    rotation_center: tuple[float, float, float] = ROTATION_CENTER,
    time_col: str = "time",
    x_cols: list[str] | None = None,
    y_cols: list[str] | None = None,
    z_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Bring OptiTrack coordinates into the gantry frame.

    The alignment shifts the time base, rotates about ``rotation_center`` and
    translates, with ``x`` holding (dt, rx, ry, rz, tx, ty, tz). It acts on the
    columns x/y/z unless ``x_cols``, ``y_cols`` and ``z_cols`` name others, as
    needed when the frame carries several sets of coordinates.
    """
    x_cols = ["x"] if x_cols is None else x_cols
    y_cols = ["y"] if y_cols is None else y_cols
    z_cols = ["z"] if z_cols is None else z_cols

    return coord_transform(
        df,
        [
            TransformShiftT(x[0], time_col, x_cols, y_cols, z_cols),
            TransformRotate("x", x[1], rotation_center, x_cols, y_cols, z_cols),
            TransformRotate("y", x[2], rotation_center, x_cols, y_cols, z_cols),
            TransformRotate("z", x[3], rotation_center, x_cols, y_cols, z_cols),
            TransformShiftXYZ(x[4], x[5], x[6], x_cols, y_cols, z_cols),
        ],
    )


def coord_calibrate(model: CorrectionModel, df: pd.DataFrame) -> pd.DataFrame:
    """Apply a correction model to gantry coordinates."""
    df_tr = df.copy()
    df_tr[["x", "y", "z"]] = model.apply(df[["x", "y", "z"]].to_numpy())
    return df_tr


def correction_terms(degree: Degree = DEFAULT_DEGREE) -> list[tuple[int, int]]:
    """Terms of the correction model besides the constant, as (power, axis) pairs.

    The terms are ordered by power, and by axis within each power. With the default
    degree (2, 2, 1) they are x, y, z, x**2 and y**2 and the returned value is
    [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]
    """
    return [
        (power, axis)
        for power in range(1, max(degree) + 1)
        for axis in range(3)
        if power <= degree[axis]
    ]


def design_matrix(gantry: np.ndarray, degree: Degree = DEFAULT_DEGREE) -> np.ndarray:
    """Design matrix of the correction model for a set of gantry positions.

    The columns are the terms of ``correction_terms`` followed by a column of ones,
    so each row of the least squares solution against the OptiTrack positions holds
    the column of A that multiplies its term, and c in the last one.
    """
    cols = [gantry[:, axis] ** power for power, axis in correction_terms(degree)]
    return np.column_stack(cols + [np.ones(len(gantry))])


def correction_params_from_coef(
    coef: np.ndarray, degree: Degree, scale: np.ndarray
) -> CorrectionParams:
    """Parameters of the correction model from the coefficients of a fit.

    ``coef`` has one row per column of the design matrix, built from the gantry
    positions divided by ``scale``. The scaling is undone here, so the parameters
    apply to the positions as they are.
    """
    mat_a = np.zeros((max(degree), 3, 3))
    for row, (k, axis) in zip(coef, correction_terms(degree)):
        mat_a[k - 1, :, axis] = row / scale[axis] ** k
    return CorrectionParams.model_validate(
        {"c": coef[-1].tolist(), "A": mat_a.tolist()}
    )


def correction_scale(gantry: np.ndarray) -> np.ndarray:
    """Scale of each coordinate that brings the gantry positions to [-1, 1].

    The correction model is fitted on the scaled positions. In millimeters the
    columns of the design matrix span too many orders of magnitude (x**3 reaches
    1e11 against the column of ones), which makes the matrix ill-conditioned.
    ``numpy.linalg.lstsq`` treats as zero the singular values below the value
    specified in the `rcond` parameter. The default value for `rcond` (when None
    is specified) is the machine precision times the number of samples.
    """
    scale = np.nanmax(np.abs(gantry), axis=0)
    scale[scale == 0] = 1.0
    return scale


def fit_correction_params(
    gantry: np.ndarray, optitrack: np.ndarray, degree: Degree = DEFAULT_DEGREE
) -> CorrectionParams:
    """Least squares fit of the correction model that maps gantry onto optitrack.

    The samples must be free of NaN.
    """
    scale = correction_scale(gantry)
    design = design_matrix(gantry / scale, degree)
    coef, _, _, _ = np.linalg.lstsq(design, optitrack, rcond=None)
    return correction_params_from_coef(coef, degree, scale)


def reject_samples(
    gantry: np.ndarray,
    optitrack: np.ndarray,
    time: np.ndarray,
    sigma: float = 5.0,
    margin_s: float = 0.25,
    iterations: int = 2,
    degree: Degree = DEFAULT_DEGREE,
) -> np.ndarray:
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
    Returns the mask of the samples to keep.
    """
    keep = np.ones(len(gantry), dtype=bool)

    for _ in range(max(iterations, 1)):
        params = fit_correction_params(gantry[keep], optitrack[keep], degree)
        residual = np.linalg.norm(params.apply(gantry) - optitrack, axis=1)
        median = np.median(residual)
        spread = np.median(np.abs(residual - median)) * 1.4826
        rejected = residual >= median + sigma * spread

        if margin_s > 0 and rejected.any():
            # Each rejected sample widens into the interval of samples within
            # margin_s of it, and the mask is the union of those intervals. Every
            # interval contributes one +1 and one -1 to the edge count, so the
            # running sum gives how many of them cover each sample.
            start = np.searchsorted(time, time[rejected] - margin_s, side="left")
            end = np.searchsorted(time, time[rejected] + margin_s, side="right")
            edges = np.zeros(len(time) + 1, dtype=int)
            np.add.at(edges, start, 1)
            np.add.at(edges, end, -1)
            rejected = np.cumsum(edges[:-1]) > 0

        keep = ~rejected

    return keep


def interp_columns(t: np.ndarray, t_src: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Resample the columns of ``values``, taken at ``t_src``, onto the times ``t``.

    ``values`` has one row per sample of ``t_src`` and any number of columns,
    each interpolated independently. Times outside the range covered by
    ``t_src`` are returned as NaN.
    """
    values = np.asarray(values)
    return np.column_stack(
        [
            np.interp(t, t_src, values[:, i], left=np.nan, right=np.nan)
            for i in range(values.shape[1])
        ]
    )


# Objective to minimize when fitting the alignment/correction parameters
Objective = Literal["mse", "mean_distance"]


class MinimizeOptions(BaseModel):
    # Options for scipy.optimize.minimize.
    # Method should be one of the supported by scipy.optimize.minimize
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
    method: Literal[
        "Nelder-Mead",
        "Powell",
        "CG",
        "BFGS",
        "Newton-CG",
        "L-BFGS-B",
        "TNC",
        "COBYLA",
        "COBYQA",
        "SLSQP",
        "trust-constr",
        "dogleg",
        "trust-ncg",
        "trust-exact",
        "trust-krylov",
    ] = "Powell"
    tolerance: float = 1e-9
    display: bool = True


class CalibrationAlignmentConfig(BaseModel):
    enabled: bool = True
    init_params: list[float] | None = None
    max_rotation: float | None = np.pi / 32
    rotation_center: tuple[float, float, float] = ROTATION_CENTER
    objective: Objective = "mse"
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
    # Highest power of x, y and z in the correction model. See CorrectionParams.
    degree: Degree = DEFAULT_DEGREE
    init_params: list[float] | None = None
    objective: Objective = "mse"
    minimize_options: MinimizeOptions = Field(default_factory=MinimizeOptions)
    reject_samples: RejectSamplesConfig = Field(default_factory=RejectSamplesConfig)
    skip_samples: SkipSamplesConfig = Field(default_factory=SkipSamplesConfig)


class CalibrationConfig(BaseModel):
    alignment: CalibrationAlignmentConfig = Field(
        default_factory=CalibrationAlignmentConfig
    )
    correction: CalibrationCorrectionConfig = Field(
        default_factory=CalibrationCorrectionConfig
    )


class CalibrationParams(BaseModel):
    alignment: list[float] | None = None
    correction: CorrectionParams | None = None


def load_correction_params(filename: str | Path) -> CorrectionParams:
    """Load the parameters of the correction model from a file."""
    with open(filename, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    if calibration_params.correction is None:
        raise ValueError(f"No correction parameters in {filename}")

    return calibration_params.correction


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

    rotation_center = config.alignment.rotation_center

    alignment_params_array: np.ndarray | None = None
    if config.alignment.enabled and calibration_params.alignment is not None:
        alignment_params_array = np.array(calibration_params.alignment)
    elif config.alignment.enabled:
        # Gantry data
        df_g_xyz: pd.DataFrame = df.loc[:, ["time", "GAN.X", "GAN.Y", "GAN.Z"]]
        df_g_xyz.columns = pd.Index(["time", "x", "y", "z"])

        # OptiTrack data
        df_o_xyz: pd.DataFrame = df.loc[:, ["time", "RB.X", "RB.Y", "RB.Z"]]
        df_o_xyz.columns = pd.Index(["time", "x", "y", "z"])

        # Initial alignment parameters
        if config.alignment.init_params:
            x0 = np.array(config.alignment.init_params)
        else:
            x0 = np.zeros(7)

        bounds: list[tuple[float | None, float | None]] | None = None

        if max_rotation := config.alignment.max_rotation:
            bounds = [(None, None) for _ in range(len(x0))]
            bounds[1] = (x0[1] - max_rotation, x0[1] + max_rotation)
            bounds[2] = (x0[2] - max_rotation, x0[2] + max_rotation)
            bounds[3] = (x0[3] - max_rotation, x0[3] + max_rotation)

        objective_fn = (
            coord_mse if config.alignment.objective == "mse" else coord_mean_distance
        )
        min_opts = config.alignment.minimize_options

        def opt_callback(intermediate_result):
            if min_opts.display:
                fval = getattr(intermediate_result, "fun", intermediate_result)
                print(f"fval: {fval}")

        logger.info("Aligning OptiTrack data with gantry data...")
        res = scp.optimize.minimize(  # type: ignore[call-overload]
            fun=lambda x: objective_fn(
                df_g_xyz, coord_align(x, df_o_xyz, rotation_center)
            ),
            x0=x0,
            bounds=bounds,
            tol=min_opts.tolerance,
            options={"disp": min_opts.display},
            callback=opt_callback,
            method=min_opts.method,
        )

        alignment_params_array = res.x
        logger.info("Alignment completed. Parameters: %s", alignment_params_array)

        df_o_aligned = coord_align(res.x, df_o_xyz, rotation_center)
        mean_dist_err = coord_mean_distance(df_g_xyz, df_o_aligned)
        mean_sq_err = coord_mse(df_g_xyz, df_o_aligned)

        logger.info("Alignment mean distance error: %f", mean_dist_err)
        logger.info("Alignment mean square error: %f", mean_sq_err)

    if alignment_params_array is not None:
        # Transform all the OptiTrack coordinates in the dataframe
        cols_params = {
            f"{axis.lower()}_cols": [
                col
                for col in df.columns
                if col.startswith((f"M.{axis}", f"RB.{axis}"))
            ]
            for axis in ["X", "Y", "Z"]
        }

        df = coord_align(
            alignment_params_array,
            df,
            rotation_center,
            x_cols=cols_params["x_cols"],
            y_cols=cols_params["y_cols"],
            z_cols=cols_params["z_cols"],
        )

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
        mat_g_xyz = df[["GAN.X", "GAN.Y", "GAN.Z"]].to_numpy()
        mat_o_xyz = df[["RB.X", "RB.Y", "RB.Z"]].to_numpy()
        mat_t = df["time"].to_numpy()
        valid = ~(np.isnan(mat_g_xyz).any(axis=1) | np.isnan(mat_o_xyz).any(axis=1))
        valid = cast(np.typing.NDArray[np.bool], valid)

        reject_opts = config.correction.reject_samples
        keep = reject_samples(
            mat_g_xyz[valid],
            mat_o_xyz[valid],
            mat_t[valid],
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
    # Calculate and apply non-linear coordinate transformation to correct the
    # misalignments between the gantry and the OptiTrack system.
    #
    # We consider the following transformation:
    #
    #   pos_optitrack = c + pos_gantry @ A_1.T + ... + pos_gantry ** n @ A_n.T
    #
    # where:
    #   - pos_gantry is the position of the gantry (row vector)
    #   - pos_optitrack is the position of the OptiTrack system (row vector)
    #   - A_1, ..., A_n are 3x3 matrices
    #   - c is a 3x1 vector
    #
    # The parameters are the vector c and the elements of the matrices A_k, in
    # the columns of the powers that the degree of the configuration allows.
    # See CorrectionParams.
    # -------------------------------------------------------------------------

    correction_params: CorrectionParams | None = None
    degree = config.correction.degree

    if config.correction.enabled and calibration_params.correction is not None:
        correction_params = calibration_params.correction

        if correction_params.degree != max(degree):
            logger.warning(
                "The correction parameters are of degree %d, but the degree of the "
                "configuration is %s",
                correction_params.degree,
                degree,
            )
    elif config.correction.enabled:
        # Gantry data
        df_g_xyz = df.loc[:, ["time", "GAN.X", "GAN.Y", "GAN.Z"]]
        df_g_xyz.columns = pd.Index(["time", "x", "y", "z"])

        # OptiTrack data
        df_o_xyz = df.loc[:, ["time", "RB.X", "RB.Y", "RB.Z"]]
        df_o_xyz.columns = pd.Index(["time", "x", "y", "z"])

        logger.info("Correcting gantry data...")
        mat_g_xyz = df_g_xyz[["x", "y", "z"]].to_numpy()
        mat_o_xyz = df_o_xyz[["x", "y", "z"]].to_numpy()

        valid = ~(np.isnan(mat_g_xyz).any(axis=1) | np.isnan(mat_o_xyz).any(axis=1))
        mat_g_xyz, mat_o_xyz = mat_g_xyz[valid], mat_o_xyz[valid]

        if config.correction.objective == "mse":
            # The correction model is linear in c and the matrices A_k, so we
            # use linear least squares to minimize the mean square error.
            correction_params = fit_correction_params(mat_g_xyz, mat_o_xyz, degree)
        else:
            # The parameters to optimize are the coefficients of the model on the
            # scaled gantry positions, one row of three per term and one for c
            # (see correction_scale). The initial point is the identity.
            terms = correction_terms(degree)
            scale = correction_scale(mat_g_xyz)
            coef0 = np.zeros((len(terms) + 1, 3))
            for row, (k, axis) in enumerate(terms):
                if k == 1:
                    coef0[row, axis] = scale[axis]

            mat_d = design_matrix(mat_g_xyz / scale, degree)

            def mean_distance(x: np.ndarray) -> float:
                err = mat_d @ x.reshape(-1, 3) - mat_o_xyz
                return float(np.sqrt((err**2).sum(axis=1)).mean())

            min_opts = config.correction.minimize_options

            def opt_callback(intermediate_result):
                if min_opts.display:
                    fval = getattr(intermediate_result, "fun", intermediate_result)
                    print(f"fval: {fval}")

            res = scp.optimize.minimize(  # type: ignore[call-overload]
                fun=mean_distance,
                x0=coef0.flatten(),
                tol=min_opts.tolerance,
                options={"disp": min_opts.display},
                callback=opt_callback,
                method=min_opts.method,
            )

            if not res.success:
                logger.warning("The correction fit did not converge: %s", res.message)

            correction_params = correction_params_from_coef(
                res.x.reshape(-1, 3), degree, scale
            )

        df_g_correct = coord_calibrate(correction_params, df_g_xyz)
        mean_dist_err = coord_mean_distance(df_o_xyz, df_g_correct)
        mean_sq_err = coord_mse(df_o_xyz, df_g_correct)

        logger.info("Correction completed. Parameters: %s", correction_params)
        logger.info("Correction mean distance error: %f", mean_dist_err)
        logger.info("Correction mean square error: %f", mean_sq_err)

    if correction_params is not None:
        df_correct: pd.DataFrame = df.loc[:, ["GAN.X", "GAN.Y", "GAN.Z"]]
        df_correct.columns = pd.Index(["x", "y", "z"])
        df_correct = coord_calibrate(correction_params, df_correct)

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

    def np_to_list(x: np.ndarray | None) -> list[float] | None:
        return x.tolist() if x is not None else None

    calibration_params = CalibrationParams(
        alignment=np_to_list(alignment_params_array),
        correction=correction_params,
    )

    # -------------------------------------------------------------------------
    # Return the processed data
    # -------------------------------------------------------------------------

    return df, calibration_params, num_markers
