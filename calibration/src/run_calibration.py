import argparse
import logging
import os
import sys

from data import get_processed_data, CalibrationConfig, CalibrationParams

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Run alignment and calibration of the OptiTrack data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to the CSV file with the OptiTrack movement data",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to CSV file with the gantry movement data",
    )

    parser.add_argument(
        "--config",
        help="Path to the calibration configuration file",
        type=str,
        default="config.json",
    )

    parser.add_argument(
        "--calibration",
        help="Path to save the calibration parameters file",
        type=str,
        default="calibration.json",
    )

    args = parser.parse_args()

    if os.path.exists(args.calibration):
        response = input(
            "Calibration file already exists. Run calibration again? (y/N): "
        )
        if response.lower() != "y":
            print("Exiting...")
            sys.exit(0)
    
    calibration_params = CalibrationParams()

    if os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = CalibrationConfig.model_validate_json(f.read())
            print("Loaded calibration configuration from", args.config)
    else:
        config = CalibrationConfig()
        print("No calibration configuration file found. Using default configuration.")

    # Get the calibrated data and parameters
    df_calibrated, calibration_params_out, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        calibration_params=calibration_params,
        config=config,
    )

    # Save the calibration parameters
    with open(args.calibration, "w") as f:
        f.write(calibration_params_out.model_dump_json(indent=2))
    print("Calibration parameters saved to", args.calibration)