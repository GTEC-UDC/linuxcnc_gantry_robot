import argparse

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
            print(df[err_cols].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]))

    for label, pos_prefix, err_prefix in SETS:
        err_cols = [f"{err_prefix}{c}" for c in ["X", "Y", "Z"]]
        if df[err_cols].notna().to_numpy().any():
            print(f"\nError correlation ({label}):")
            print(df[err_cols].corr())

            print(f"\nError covariance ({label}):")
            print(df[err_cols].cov())


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
        "--skip-samples",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the sample exclusions of the configuration file",
    )

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = CalibrationConfig.model_validate_json(f.read())

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    config.correction.skip_samples.enabled = args.skip_samples
    config.correction.reject_samples.enabled = args.skip_samples

    df, _, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        config=config,
        calibration_params=calibration_params,
    )

    print_summary(df)
