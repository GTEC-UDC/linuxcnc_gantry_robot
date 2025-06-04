import json
import logging
import os
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Optional, cast

import numpy as np
import pandas as pd
import scipy as scp

from coordinates_utils import (
    TransformRotateCenter,
    TransformShiftT,
    TransformShiftXYZ,
    coord_matrix_transform2,
    coord_mse,
    coord_transform,
)

logger = logging.getLogger(__name__)


def load_bad_frames(filename: str) -> list[tuple[int, int]]:
    """Load bad frame ranges from a JSON file.

    Args:
        filename (str): Path to the JSON file containing bad frame ranges.

    Returns:
        list[tuple[int, int]]: List of tuples where each tuple contains the start and end
            frame numbers of a range of bad frames.
    """
    with open(filename, "r") as f:
        data = json.load(f)

    return [tuple(range) for range in data.get("ranges", [])]


def load_gantry_data(filename: str) -> pd.DataFrame:
    """Load gantry position data from a CSV file.

    Args:
        filename (str): Path to the CSV file containing gantry data.

    Returns:
        pd.DataFrame: DataFrame containing the gantry position data.
    """
    return cast(pd.DataFrame, pd.read_csv(filename))


def load_optitrack_metadata(filename: str) -> dict[str, Any]:
    """Load and parse OptiTrack metadata from a CSV file.

    This function reads the first line of an OptiTrack CSV file and parses the metadata
    information, including capture frame rate, export frame rate, start frame, total frames,
    and capture start time.

    Args:
        filename (str): Path to the OptiTrack CSV file.

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
    metadata["Capture Start Time"] = datetime.strptime(capture_date_str, date_format)

    return metadata


def load_optitrack_data(
    filename: str, rigid_body_name: Optional[str] = None
) -> tuple[pd.DataFrame, int]:
    """Load and process OptiTrack motion capture data from a CSV file.

    This function loads OptiTrack data, processes marker positions, calculates errors
    between raw and rigid body markers, and computes various statistics.

    Args:
        filename (str): Path to the OptiTrack CSV file.
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
    df = pd.read_csv(filename, header=[1, 2, 4, 5])

    # Get the columns we want to keep and create new names
    df_cols = list(df.columns[:2])
    df_col_names = ["frame", "time"]
    num_rb_m = 0
    num_m = 0

    if rigid_body_name is None:
        rigid_body_name = df.columns[2][1]
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
    df = df[df_cols]
    df.columns = df_col_names

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
        df_cols = df[cols]

        # Interpolate the optitrack data to fill the missing values
        df_cols = df_cols.interpolate(
            method="linear", axis=0, limit_area="inside", inplace=False
        )

        df[f"M.{coord}_centroid"] = df_cols.mean(axis=1)

    # Set to NA the coordinates where no raw markers were detected
    m_centroid_cols = [f"M.{coord}_centroid" for coord in ["X", "Y", "Z"]]
    df.loc[raw_markers_na, m_centroid_cols] = np.nan

    rb_cols = ["RB.X", "RB.Y", "RB.Z"] + [
        f"RB.{coord}{i}" for i in range(1, num_m + 1) for coord in ["X", "Y", "Z"]
    ]
    df.loc[raw_markers_na, rb_cols] = np.nan

    return df, num_m


def get_calibration_matrices(x) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert calibration parameters into transformation matrices.

    Args:
        x: Array of calibration parameters (18 elements).

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing:
            - 3x3 transformation matrix for the first transformation
            - 3x3 transformation matrix for the second transformation
            - 3-element translation array
    """
    matrix1 = np.array(x[:9]).reshape(3, 3)
    matrix2 = np.array(np.concatenate([x[9:15], [0, 0, 0]])).reshape(3, 3)
    array = np.array(x[15:18])
    return matrix1, matrix2, array


def get_processed_data(
    gantry_filename: str,
    optitrack_filename: str,
    alignment_params_filename: Optional[str] = None,
    calibration_params_filename: Optional[str] = None,
    bad_frames: Optional[list[tuple[int, int]]] = None,
    alignment_init_params: Optional[Sequence[float]] = None,
    calibrate: bool = False,
) -> tuple[pd.DataFrame, int]:
    """Process and align gantry and OptiTrack data.

    This function loads gantry and OptiTrack data, aligns them temporally and spatially,
    handles bad frames, and optionally performs calibration, i.e., correct
    misalignments between the gantry and the OptiTrack system.

    Args:
        gantry_filename (str): Path to the gantry data CSV file.
        optitrack_filename (str): Path to the OptiTrack data CSV file.
        alignment_params_filename (Optional[str], optional): Path to save/load alignment
            parameters. Defaults to None.
        calibration_params_filename (Optional[str], optional): Path to save/load
            calibration parameters. Defaults to None.
        bad_frames (Optional[list[tuple[int, int]]], optional): List of frame ranges to
            exclude. Defaults to None.
        alignment_init_params (Optional[Sequence[float]], optional): Initial alignment
            parameters. Defaults to None.
        calibrate (bool, optional): Whether to perform calibration. Defaults to False.

    Returns:
        tuple[pd.DataFrame, int]: A tuple containing:
            - DataFrame with processed and aligned data
            - Number of markers detected
    """
    # -------------------------------------------------------------------------
    # Load the Gantry and Optitrack data
    # -------------------------------------------------------------------------

    df_optitrack, num_markers = load_optitrack_data(optitrack_filename)
    metadata_optitrack = load_optitrack_metadata(optitrack_filename)

    df_gantry = load_gantry_data(gantry_filename)

    # -------------------------------------------------------------------------
    # Combine the data
    # -------------------------------------------------------------------------

    capture_start_time = metadata_optitrack["Capture Start Time"].timestamp()

    df = df_optitrack.copy()
    t_o = df_optitrack["time"]
    t_g = df_gantry["time"] - capture_start_time

    df["GAN.X"] = np.interp(t_o, t_g, df_gantry["x"], left=np.nan, right=np.nan)
    df["GAN.Y"] = np.interp(t_o, t_g, df_gantry["y"], left=np.nan, right=np.nan)
    df["GAN.Z"] = np.interp(t_o, t_g, df_gantry["z"], left=np.nan, right=np.nan)

    # -------------------------------------------------------------------------
    # Align the optitrack data with the gantry data
    #
    # The optitrack data is rotated and translated to align it with the gantry
    # data. The alignment parameters are saved in the alignment_params_filename
    # file. If the file exists, the alignment parameters are loaded from the file,
    # otherwise, the alignment parameters are calculated using the Powell method.
    # -------------------------------------------------------------------------

    # File for the alignment parameters
    if alignment_params_filename and os.path.exists(alignment_params_filename):
        alignment_params = np.load(alignment_params_filename)
        logger.info("Alignment parameters loaded from file: %s", alignment_params)
    else:
        # Function to transform the data based on an array of parameters
        def coord_transform_array(x, df: pd.DataFrame) -> pd.DataFrame:
            return coord_transform(
                df,
                [
                    TransformShiftXYZ(x[0], x[1], x[2]),
                    TransformRotateCenter("x", x[3]),
                    TransformRotateCenter("y", x[4]),
                    TransformRotateCenter("z", x[5]),
                    TransformShiftT(x[6]),
                ],
            )

        # Gantry data
        df_gantry_tr = df[["time", "GAN.X", "GAN.Y", "GAN.Z"]]
        df_gantry_tr.columns = ["time", "x", "y", "z"]

        # Optitrack data
        df_optitrack_tr = df[["time", "RB.X", "RB.Y", "RB.Z"]]
        df_optitrack_tr.columns = ["time", "x", "y", "z"]

        # Initial alignment parameters
        if alignment_init_params:
            x0 = np.array(alignment_init_params)
        else:
            x0 = np.zeros(7)

        bounds: list[tuple[float | None, float | None]] = [(None, None)] * len(x0)
        bounds[3] = (x0[3] - np.pi / 32, x0[3] + np.pi / 32)
        bounds[4] = (x0[4] - np.pi / 32, x0[4] + np.pi / 32)
        bounds[5] = (x0[5] - np.pi / 32, x0[5] + np.pi / 32)

        logger.info("Aligning optitrack data with gantry data...")
        res = scp.optimize.minimize(
            fun=lambda x: coord_mse(
                df_gantry_tr, coord_transform_array(x, df_optitrack_tr)
            ),
            x0=x0,
            bounds=bounds,
            tol=1e-9,
            options={"disp": True},
            callback=lambda intermediate_result: print(
                f"fval: {getattr(intermediate_result, 'fun', intermediate_result)}"
            ),
            method="Powell",
        )

        alignment_params = res.x
        logger.info("Alignment completed. Parameters: %s", alignment_params)

        # save the alignment parameters
        if alignment_params_filename:
            np.save(alignment_params_filename, alignment_params)

    # Transform all the optitrack data in the dataframe
    center_cols = ["RB.X", "RB.Y", "RB.Z"]
    cols_params = {
        f"{axis.lower()}_cols": [
            col
            for col in df.columns
            if col.startswith(f"M.{axis}") or col.startswith(f"RB.{axis}")
        ]
        for axis in ["X", "Y", "Z"]
    }

    df = coord_transform(
        df,
        [
            TransformShiftXYZ(
                alignment_params[0],
                alignment_params[1],
                alignment_params[2],
                **cols_params,
            ),
            TransformRotateCenter("x", alignment_params[3], center_cols, **cols_params),
            TransformRotateCenter("y", alignment_params[4], center_cols, **cols_params),
            TransformRotateCenter("z", alignment_params[5], center_cols, **cols_params),
            TransformShiftT(alignment_params[6], "time", **cols_params),
        ],
    )

    # -------------------------------------------------------------------------
    # Remove bad frames
    # -------------------------------------------------------------------------

    # Note: We remove the bad frames after the alignment to avoid problems.
    # Consider that the alignment parameters are calculated using the whole
    # data, including the bad frames, then removing some bad frames before
    # applying the alignment may yield invalid results. This is due to the fact
    # that there are several TransformRotateCenter transformations whose results
    # depend on the data.

    if bad_frames:
        coord_cols = [col for col in df.columns if col not in ("time", "frame")]
        for start, end in bad_frames:
            df.loc[start:end, coord_cols] = np.nan

    # -------------------------------------------------------------------------
    # Calculate and apply calibration to the optitrack data
    #
    # The calibration is performed to correct the misalignments between the
    # gantry and the OptiTrack system. The calibration parameters are saved in
    # the calibration_params_filename file. If the file exists, the calibration
    # parameters are loaded from the file, otherwise, the calibration parameters
    # are calculated using the Powell method.
    #
    # To obtain the calibration parameters, we consider the following
    # transformation:
    #
    #   pos_optitrack = pos_gantry * A + pos_gantry ** 2 * B + C
    #
    # where:
    #   - pos_gantry is the position of the gantry (row vector)
    #   - pos_optitrack is the position of the OptiTrack system (row vector)
    #   - A is a 3x3 matrix
    #   - B is a 3x3 matrix
    #   - C is a 3x1 vector
    #
    # The calibration parameters are the elements of the matrices A, B, and C.
    # -------------------------------------------------------------------------

    calibration_params: Optional[np.ndarray] = None

    if (
        calibrate
        and calibration_params_filename
        and os.path.exists(calibration_params_filename)
    ):
        calibration_params = np.load(calibration_params_filename)
        logger.info("Calibration parameters loaded from file: %s", calibration_params)
    elif calibrate:
        # Function to transform the data based on an array of parameters
        def coord_transform_array(x, df: pd.DataFrame) -> pd.DataFrame:
            matrix1, matrix2, array = get_calibration_matrices(x)
            return coord_matrix_transform2(df, matrix1, matrix2, array)

        # Gantry data
        df_gantry_tr = df[["time", "GAN.X", "GAN.Y", "GAN.Z"]]
        df_gantry_tr.columns = ["time", "x", "y", "z"]

        # Optitrack data
        df_optitrack_tr = df[["time", "RB.X", "RB.Y", "RB.Z"]]
        df_optitrack_tr.columns = ["time", "x", "y", "z"]

        x0 = np.zeros(18)
        x0[[0, 4, 8]] = 1

        logger.info("Calibrating gantry data...")
        res = scp.optimize.minimize(
            fun=lambda x: coord_mse(
                df_optitrack_tr, coord_transform_array(x, df_gantry_tr)
            ),
            x0=x0,
            tol=1e-9,
            options={"disp": True},
            callback=lambda intermediate_result: logger.info(
                "fval: %s",
                getattr(intermediate_result, "fun", intermediate_result),
            ),
            method="Powell",
        )

        calibration_params = cast(np.ndarray, res.x)
        logger.info("Calibration completed. Parameters: %s", calibration_params)

        # save the calibration parameters
        if calibration_params_filename:
            np.save(calibration_params_filename, calibration_params)

    if calibration_params is not None:
        df_calib = df[["GAN.X", "GAN.Y", "GAN.Z"]]
        df_calib.columns = ["x", "y", "z"]

        m1, m2, vec = get_calibration_matrices(calibration_params)
        df_calib = coord_matrix_transform2(df_calib, m1, m2, vec)

        # Add calibrated coordinates to the dataframe
        df["GAN.CALIBRATED.X"] = df_calib["x"]
        df["GAN.CALIBRATED.Y"] = df_calib["y"]
        df["GAN.CALIBRATED.Z"] = df_calib["z"]
    else:
        # Add calibrated coordinates with nan values
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
    # Return the processed data
    # -------------------------------------------------------------------------

    return df, num_markers
