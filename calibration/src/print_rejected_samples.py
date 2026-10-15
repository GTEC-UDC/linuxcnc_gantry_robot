"""Print the samples excluded from the correction fit and the markers in them.

The samples are excluded in two ways (see ``get_processed_data``): the ranges of
``skip_samples`` in the configuration file, and the automatic rejection of
``reject_samples``. This script lists the rejected intervals with their largest
residual and the number of platform markers that OptiTrack reconstructed in them,
and compares the markers of the retained and the rejected samples.

The residual is the distance between the corrected gantry position and the aligned
OptiTrack position, with the parameters of the calibration file. It is computed on a
second pass without exclusions, because the excluded samples are NaN.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from data import CalibrationConfig, CalibrationParams, get_processed_data
from defaults import CALIBRATION_FILE, CONFIG_FILE, GANTRY_FILE, OPTITRACK_FILE


def print_rejected_samples(
    df: pd.DataFrame, df_all: pd.DataFrame, num_markers: int
) -> None:
    """Print the rejected intervals and the marker statistics.

    Args:
        df: Processed data with the exclusions applied.
        df_all: Processed data without exclusions, with the same rows as ``df``.
        num_markers: Number of markers of the platform rigid body.
    """
    gan = df_all[["GAN.CALIBRATED.X", "GAN.CALIBRATED.Y", "GAN.CALIBRATED.Z"]]
    rb = df_all[["RB.X", "RB.Y", "RB.Z"]]
    residual = np.linalg.norm(gan.to_numpy() - rb.to_numpy(), axis=1)
    valid = ~np.isnan(residual)

    skipped = df["SKIPPED"].to_numpy() & valid
    rejected = df["REJECTED"].to_numpy()
    retained = df[["GAN.X", "RB.X"]].notna().all(axis=1).to_numpy()
    count = df["M.COUNT"].to_numpy()
    time = df["time"].to_numpy()

    # Intervals of consecutive rejected samples among the samples with both
    # records, as reject_samples() sees them
    idx = np.flatnonzero(valid)
    rej = rejected[idx]
    edges = np.diff(np.r_[0, rej.astype(int), 0])
    starts = idx[np.flatnonzero(edges == 1)]
    ends = idx[np.flatnonzero(edges == -1) - 1]

    n_valid = int(valid.sum())
    n_checked = n_valid - int(skipped.sum())  # samples seen by reject_samples()
    print("Samples:")
    print(f"  with gantry and OptiTrack positions:  {n_valid}")
    print(f"  skipped:                              {int(skipped.sum())}")
    print(
        f"  rejected:                             {int(rejected.sum())} of "
        f"{n_checked} ({100 * rejected.sum() / n_checked:.2f} %), "
        f"in {len(starts)} intervals"
    )
    print(f"  retained:                             {int(retained.sum())}")
    print()

    print(f"Number of markers of the rigid body: {num_markers}")

    if len(starts):
        print()
        print("Rejected intervals:")
        print(
            "  start (s)   end (s)  samples  max residual (mm)  markers (%)  mean markers"
        )
        for a, b in zip(starts, ends):
            c = count[a : b + 1]
            print(
                f"  {time[a]:9.2f} {time[b]:9.2f} {b - a + 1:8d} "
                f"{np.nanmax(residual[a : b + 1]):18.1f} "
                f"{100 * (c == num_markers).mean():12.1f} {c.mean():13.2f}"
            )

    print("\nMarkers reconstructed:")
    for label, mask in [("retained", retained), ("rejected", rejected)]:
        if mask.any():
            c = count[mask]
            print(
                f"  {label} samples: mean {c.mean():.2f} markers per sample; "
                f"{100 * (c == num_markers).mean():.1f} % of the samples "
                f"with all the markers"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Print the samples rejected from the correction fit and the markers "
            "reconstructed in them"
        ),
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

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    df, _, num_markers = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    config.correction.skip_samples.enabled = False
    config.correction.reject_samples.enabled = False

    df_all, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    print_rejected_samples(df, df_all, num_markers)
