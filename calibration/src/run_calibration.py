import argparse
import json
import logging
import os
import sys

from data import get_processed_data, load_bad_frames

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Run alignment and calibration of the Optitrack data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--optitrack",
        type=str,
        default="take_optitrack.csv",
        help="Path to the CSV file with the Optitrack movement data",
    )

    parser.add_argument(
        "--gantry",
        type=str,
        default="take_gantry.csv",
        help="Path to CSV file with the gantry movement data",
    )

    parser.add_argument(
        "--alignment",
        help="Path to save the alignment parameters file",
        type=str,
        default="alignment_params.npy",
    )

    parser.add_argument(
        "--calibration",
        help="Path to save the calibration parameters file",
        type=str,
        default="calibration_params.npy",
    )

    parser.add_argument(
        "--remove-bad-frames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Remove bad frames from the data",
    )

    parser.add_argument(
        "--bad-frames",
        type=str,
        default="bad_frames.json",
        help="Path to bad frames data file",
    )

    parser.add_argument(
        "--alignment-init",
        type=str,
        default="alignment_init.json",
        help="Path to the alignment initial parameters file",
    )


    args = parser.parse_args()

    keep_alignment = False
    keep_calibration = False

    if os.path.exists(args.alignment):
        response = input("Alignment file already exists. Do you want to delete it? (y/N): ")
        if response.lower() == 'y':
            print("Removing existing alignment file...")
            os.remove(args.alignment)
            keep_alignment = False
        else:
            keep_alignment = True

    if os.path.exists(args.calibration):
        response = input("Calibration file already exists. Do you want to delete it? (y/N): ")
        if response.lower() == 'y':
            print("Removing existing calibration file...")
            os.remove(args.calibration)
            keep_calibration = False
        else:
            keep_calibration = True

    if keep_alignment and keep_calibration:
        print("Exiting...")
        sys.exit(0)

    bad_frames = None
    if args.remove_bad_frames and os.path.exists(args.bad_frames):
        bad_frames = load_bad_frames(args.bad_frames)

    alignment_init_params = None
    if args.alignment_init and os.path.exists(args.alignment_init):
        with open(args.alignment_init, "r") as f:
            alignment_init_params = json.load(f)

    # Get the processed data with calibration
    df_calibrated, _ = get_processed_data(
        args.gantry,
        args.optitrack,
        alignment_params_filename=args.alignment,
        calibration_params_filename=args.calibration,
        bad_frames=bad_frames,
        alignment_init_params=alignment_init_params,
        calibrate=True,
    )
