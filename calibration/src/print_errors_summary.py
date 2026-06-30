import argparse
from typing import cast

import pandas as pd
from data import CalibrationConfig, CalibrationParams, get_processed_data

SETS = [
    ("Non corrected", "GAN.", "GAN.ERR."),
    ("Corrected", "GAN.CALIBRATED.", "GAN.ERR.CALIBRATED."),
]


def print_summary(df: pd.DataFrame) -> None:
    for label, pos_prefix, err_prefix in SETS:
        err_cols = [f"{err_prefix}{c}" for c in ["X", "Y", "Z", "Abs"]]
        if df[err_cols].notna().to_numpy().any():
            print(f"\nStatistical Summary ({label}):")
            print(df[err_cols].describe())

    for label, pos_prefix, err_prefix in SETS:
        pos_cols = [f"{pos_prefix}{c}" for c in ["X", "Y", "Z"]]
        err_cols = [f"{err_prefix}{c}" for c in ["X", "Y", "Z"]]
        if df[err_cols].notna().to_numpy().any():
            print(f"\nR-squared values ({label}):")
            for pos in pos_cols:
                for err in err_cols:
                    mask = df.loc[:, [pos, err]].notna().all(axis=1)
                    if mask.any():
                        correlation = cast(
                            float, df.loc[mask, [pos, err]].corr().iloc[0, 1]
                        )
                        print(f"  {pos} vs {err}: {correlation**2:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Print statistical summary of positioning errors (raw and calibrated)"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to Optitrack CSV file",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to Gantry CSV file",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to the calibration configuration file",
    )

    parser.add_argument(
        "--calibration",
        type=str,
        default="calibration.json",
        help="Path to the calibration parameters file",
    )

    parser.add_argument(
        "--skip-frames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable skipping the frames set in the configuration file",
    )

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.skip_frames.enabled = args.skip_frames

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    print_summary(df)
