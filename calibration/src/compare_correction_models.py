"""Alternatives to the correction model of the paper, fitted on the same capture.

The model in use has linear terms, the pure squares x**2 and y**2, and a constant.
This script fits richer and poorer variants on the same aligned calibration capture
and reports what each one is worth: an affine map, the model in use, the same model
with z**2 restored, and full quadratics with the interaction terms xy, xz and yz.

Every variant is linear in its parameters, so all of them are solved by the same
least squares call, and the comparison is unaffected by any optimizer setting. Two
figures are reported per variant: the in-sample residual, and a spatial
cross-validation that leaves out one cell of a grid in the XY plane at a time and
evaluates on it, which penalizes terms that only fit the noise of their own region.

The condition number of each design matrix is reported as well, both as built (in
millimeters) and after centering and scaling its columns, which separates poor
scaling from an actual near-degeneracy of the terms.

Read-only: it does not modify the dataset, the pipeline, or the paper.

Run (from this directory, using the local venv):
    .venv/bin/python compare_correction_models.py --help
"""

import argparse
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd
from data import CalibrationConfig, CalibrationParams, get_processed_data
from defaults import CALIBRATION_FILE, CONFIG_FILE, GANTRY_FILE, OPTITRACK_FILE
from estimate_calibration_clock_drift import GAN_COLS, RB_COLS, rms3d

# Each variant is a list of the terms its design matrix holds, on top of the linear
# terms x, y, z and the constant that every variant includes.
VARIANTS: dict[str, list[str]] = {
    "affine": [],
    "paper (x2, y2)": ["xx", "yy"],
    "+ z2": ["xx", "yy", "zz"],
    "+ interactions": ["xx", "yy", "xy", "xz", "yz"],
    "full quadratic": ["xx", "yy", "zz", "xy", "xz", "yz"],
}

TERMS = {
    "xx": (0, 0),
    "yy": (1, 1),
    "zz": (2, 2),
    "xy": (0, 1),
    "xz": (0, 2),
    "yz": (1, 2),
}


def design(
    gantry: npt.NDArray[np.float64], terms: list[str]
) -> npt.NDArray[np.float64]:
    """Design matrix of one variant: linear terms, its own terms, and a constant."""
    cols = [gantry] + [
        (gantry[:, i] * gantry[:, j]).reshape(-1, 1)
        for i, j in (TERMS[t] for t in terms)
    ]
    return np.column_stack(cols + [np.ones(len(gantry))])


def fit(
    mat: npt.NDArray[np.float64], optitrack: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    coef, _, _, _ = np.linalg.lstsq(mat, optitrack, rcond=None)
    return coef.astype(np.float64)


def scaled_cond(mat: npt.NDArray[np.float64]) -> float:
    """Condition number after centering and scaling the columns to unit norm.

    The constant column is left alone, since centering would annihilate it.
    """
    mat = mat[:, :-1] - mat[:, :-1].mean(axis=0)
    mat = mat / np.linalg.norm(mat, axis=0)
    return float(np.linalg.cond(np.column_stack([mat, np.ones(len(mat))])))


def cells(gantry: npt.NDArray[np.float64], n: int) -> npt.NDArray[np.integer]:
    """Index of the XY cell of an n x n grid over the workspace, for each sample."""
    idx = np.zeros(len(gantry), dtype=int)
    for axis in (0, 1):
        edges = np.linspace(gantry[:, axis].min(), gantry[:, axis].max(), n + 1)[1:-1]
        idx = idx * n + np.searchsorted(edges, gantry[:, axis])
    return idx


def cross_validate(
    gantry: npt.NDArray[np.float64],
    optitrack: npt.NDArray[np.float64],
    terms: list[str],
    n: int,
) -> float:
    """RMS over the held-out cells of a leave-one-cell-out split of the XY plane."""
    idx = cells(gantry, n)
    residuals = []
    for cell in np.unique(idx):
        held = idx == cell
        coef = fit(design(gantry[~held], terms), optitrack[~held])
        residuals.append(design(gantry[held], terms) @ coef - optitrack[held])
    return rms3d(np.concatenate(residuals))


def main(args: argparse.Namespace) -> None:
    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())
    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.alignment.minimize_options.display = False
    config.correction.minimize_options.display = False

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )
    data: pd.DataFrame = df.loc[:, RB_COLS + GAN_COLS].dropna()
    optitrack = data[RB_COLS].to_numpy()
    gantry = data[GAN_COLS].to_numpy()

    print(f"{len(gantry)} paired samples, {args.grid}x{args.grid} cells for the split")
    print(
        f"\n  {'model':16s} {'params':>6s} {'RMS3D_mm':>9s} {'sX':>6s} {'sY':>6s} "
        f"{'sZ':>6s} {'CV_mm':>7s} {'cond':>9s} {'cond_s':>8s}"
    )
    for name, terms in VARIANTS.items():
        mat = design(gantry, terms)
        err = mat @ fit(mat, optitrack) - optitrack
        sigma = err.std(axis=0, ddof=1)
        cv = cross_validate(gantry, optitrack, terms, args.grid)
        print(
            f"  {name:16s} {3 * mat.shape[1]:6d} {rms3d(err):9.3f} {sigma[0]:6.2f} "
            f"{sigma[1]:6.2f} {sigma[2]:6.2f} {cv:7.3f} "
            f"{np.linalg.cond(mat):9.1e} {scaled_cond(mat):8.1f}"
        )

    print(
        "\nRMS3D and the per-axis sigmas are in-sample, CV is on the held-out cells.\n"
        "cond is the condition number of the design matrix in millimeters, cond_s the\n"
        "same after centering and scaling its columns."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare alternatives to the correction model on the calibration capture",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--optitrack",
        type=Path,
        default=OPTITRACK_FILE,
        help="Path to Optitrack CSV file",
    )
    parser.add_argument(
        "--gantry",
        type=Path,
        default=GANTRY_FILE,
        help="Path to Gantry CSV file",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_FILE,
        help="Path to the calibration configuration file",
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        default=CALIBRATION_FILE,
        help="Path to the calibration parameters file",
    )
    parser.add_argument(
        "--grid",
        type=int,
        default=3,
        help="cells per axis of the XY grid used for the spatial cross-validation",
    )
    main(parser.parse_args())
