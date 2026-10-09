"""Compare correction models using different number of terms

This script fits correction models using different number of terms:

- complete polynomials of degree n, with all the monomials x**i * y**j * z**k of
  degree i + j + k <= n;
- the same polynomials without the powers of z above the first;
- the same again without the cross terms, such as x * y, which is the structure of
  the model in use.

Every model is linear in its parameters, so all of them are solved by the same
least squares call. Two results are shown: the in-sample residual, and a spatial
cross-validation. The cross-validation leaves out one cell of a grid in the XY
plane at a time and evaluates on it.

With the --validate option, each model is also applied to the RoboLoc-G dataset,
using the functions of ``validate_dataset.py``. Note that this is much slower,
because the alignment of the dataset is fitted again for each model.

The script also reports the condition number of each design matrix, both for
the unmodified matrix in millimeters and after centering and scaling its columns
"""

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd
import validate_dataset as vd
from data import (
    CalibrationConfig,
    CalibrationParams,
    CorrectionModel,
    correction_scale,
    get_processed_data,
)
from defaults import (
    CALIBRATION_FILE,
    CONFIG_FILE,
    DATASET_DIR,
    GANTRY_FILE,
    OPTITRACK_FILE,
)

# Columns of the processed data with the OptiTrack and the gantry positions
RB_COLS = ["RB.X", "RB.Y", "RB.Z"]
GAN_COLS = ["GAN.X", "GAN.Y", "GAN.Z"]

# A monomial x**i * y**j * z**k, given by its exponents (i, j, k). A model is the
# list of its monomials, on top of the constant that every model includes.
Monomial = tuple[int, int, int]


def complete(n: int) -> list[Monomial]:
    """Monomials of the complete polynomial of degree n."""
    exponents = product(range(n + 1), repeat=3)
    return [(i, j, k) for i, j, k in exponents if 1 <= i + j + k <= n]


def linear_z(n: int) -> list[Monomial]:
    """Monomials of degree up to n that are at most linear in z."""
    return [m for m in complete(n) if m[2] <= 1]


def no_cross_terms(n: int) -> list[Monomial]:
    """Monomials of degree up to n, at most linear in z and without cross terms."""
    return [m for m in linear_z(n) if sum(e > 0 for e in m) == 1]


# Families of models to compare, with the degrees to fit of each one
FAMILIES: list[tuple[str, Callable[[int], list[Monomial]], list[int]]] = [
    ("complete", complete, [1, 2, 3]),
    ("linear z", linear_z, [2, 3]),
    ("linear z, no cross terms", no_cross_terms, [2, 3, 4]),
]

# Format of the columns of the table of results
FORMATS = {
    "params": "{:d}",
    "RMS3D": "{:.3f}",
    "sX": "{:.2f}",
    "sY": "{:.2f}",
    "sZ": "{:.2f}",
    "cond": "{:.1e}",
    "cond_s": "{:.1f}",
    "RMSE": "{:.2f}",
    "P95": "{:.2f}",
}


def rms3d(err: npt.NDArray[np.float64]) -> float:
    """3D RMS of a set of residuals, given with one row per sample."""
    return float(np.sqrt((err**2).sum(axis=1).mean()))


def design(
    gantry: npt.NDArray[np.float64], monomials: list[Monomial]
) -> npt.NDArray[np.float64]:
    """Design matrix of a model: one column per monomial, and a constant."""
    cols = [np.prod(gantry ** np.array(m), axis=1) for m in monomials]
    return np.column_stack(cols + [np.ones(len(gantry))])


@dataclass
class FullPolynomialModel(CorrectionModel):
    """A polynomial correction model, fitted by least squares."""

    monomials: list[Monomial]
    scale: npt.NDArray[np.float64]  # the model is fitted on the positions / scale
    coef: npt.NDArray[np.float64]  # one row per column of the design matrix

    def apply(self, pos: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        return design(pos / self.scale, self.monomials) @ self.coef


def fit(
    gantry: npt.NDArray[np.float64],
    optitrack: npt.NDArray[np.float64],
    monomials: list[Monomial],
) -> FullPolynomialModel:
    """Least squares fit of a model that maps gantry onto optitrack.

    The positions are scaled as in the fit of the model in use. See
    ``data.correction_scale``.
    """
    scale = correction_scale(gantry)
    coef, _, _, _ = np.linalg.lstsq(
        design(gantry / scale, monomials), optitrack, rcond=None
    )
    return FullPolynomialModel(monomials, scale, coef.astype(np.float64))


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
    monomials: list[Monomial],
    n: int,
) -> float:
    """RMS over the held-out cells of a leave-one-cell-out split of the XY plane."""
    idx = cells(gantry, n)
    residuals = []
    for cell in np.unique(idx):
        held = idx == cell
        model = fit(gantry[~held], optitrack[~held], monomials)
        residuals.append(model.apply(gantry[held]) - optitrack[held])
    return rms3d(np.concatenate(residuals))


def validate(model: FullPolynomialModel | None) -> tuple[float, float]:
    """RMSE and 95th percentile of the platform residual on the RoboLoc-G dataset.

    Follows ``validate_dataset.py``: a single alignment for the whole campaign,
    fitted against the gantry positions corrected with the model. Without a model,
    the residual is the one against the uncorrected gantry positions.
    """
    target: vd.Target = "corrected"
    label = "after"
    if model is None:
        # The uncorrected positions do not depend on the model, but the functions
        # of validate_dataset.py need one to build the corrected ones
        target, label = "uncorrected", "before"
        model = FullPolynomialModel(
            [(1, 0, 0), (0, 1, 0), (0, 0, 1)], np.ones(3), np.eye(4, 3)
        )

    alignment = vd.fit_single_alignment("all", model, target)
    alignments = {"before": alignment, "after": alignment}
    resid = np.concatenate(
        [
            vd.process_take(take, model, [vd.FRAME_BODY], alignments)["bodies"][
                (vd.FRAME_BODY, label)
            ]["resid"]
            for take in vd.TAKES
        ]
    )
    return float(np.sqrt(np.mean(resid**2))), float(np.percentile(resid, 95))


def main(args: argparse.Namespace) -> None:
    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())
    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.alignment.minimize_options.display = False
    config.correction.minimize_options.display = False

    # Override validate_dataset.py settings
    vd.DATASET_DIR = args.dataset_dir
    vd.OPTITRACK_DIR = args.dataset_dir / "OPTITRACK_MEASUREMENTS_CSV"
    vd.GROUND_TRUTH_DIR = args.dataset_dir / "GROUND_TRUTH"

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )
    data: pd.DataFrame = df.loc[:, RB_COLS + GAN_COLS].dropna()
    optitrack = data[RB_COLS].to_numpy()
    gantry = data[GAN_COLS].to_numpy()

    rows: dict[str, dict[tuple[str, str], float]] = {}
    num_rows = 1 + sum(len(degrees) for _, _, degrees in FAMILIES)

    def add_row(
        name: str,
        params: int,
        err: npt.NDArray[np.float64],
        cv: float,
        cond: float,
        cond_s: float,
        model: FullPolynomialModel | None,
    ) -> None:
        sigma = err.std(axis=0, ddof=1)
        rows[name] = {
            ("", "params"): params,
            ("in-sample", "RMS3D"): rms3d(err),
            ("in-sample", "sX"): sigma[0],
            ("in-sample", "sY"): sigma[1],
            ("in-sample", "sZ"): sigma[2],
            ("cross-validation", "RMS3D"): cv,
            ("design matrix", "cond"): cond,
            ("design matrix", "cond_s"): cond_s,
        }
        if args.validate:
            rmse, p95 = validate(model)
            rows[name][("independent", "RMSE")] = rmse
            rows[name][("independent", "P95")] = p95

        print(f"[{len(rows)}/{num_rows}] {name}: done", file=sys.stderr)

    add_row("none", 0, gantry - optitrack, np.nan, np.nan, np.nan, None)

    for family, monomials_of, degrees in FAMILIES:
        for n in degrees:
            monomials = monomials_of(n)
            model = fit(gantry, optitrack, monomials)
            mat = design(gantry, monomials)

            add_row(
                f"{family}, n={n}",
                3 * mat.shape[1],
                model.apply(gantry) - optitrack,
                cross_validate(gantry, optitrack, monomials, args.grid),
                float(np.linalg.cond(mat)),
                scaled_cond(mat),
                model,
            )

    # The keys of the rows are tuples, which makes the columns a MultiIndex
    table = pd.DataFrame.from_dict(rows, orient="index")

    print()
    print(f"{len(gantry)} paired samples, {args.grid}x{args.grid} cells for the split")
    print()
    print(
        table.to_string(
            formatters={col: FORMATS[col[1]].format for col in table.columns},
            na_rep="-",
        )
    )

    print()
    print("Values in mm")
    print(
        "The in-sample columns are the 3D RMS of the residual and its "
        "per-axis standard deviations"
    )
    print("Cross-validation is the 3D RMS on the held-out cells.")
    print("Cond is the condition number of the design matrix in millimeters")
    print(
        "Cond_s is the condition number of the design matrix after centering "
        "and scaling its columns."
    )

    if args.validate:
        print(
            "The independent columns are the RMSE and the 95th percentile of the "
            "platform on the RoboLoc-G dataset."
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
    parser.add_argument(
        "--validate",
        action="store_true",
        help="also evaluate each model on the RoboLoc-G dataset",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATASET_DIR,
        help="dataset directory, used with --validate",
    )
    main(parser.parse_args())
