# Default paths of the files used by the scripts

from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent

# Calibration measurement
MEASUREMENT_DIR = SRC_DIR.parent / "measurements/2025-04-09"
GANTRY_FILE = MEASUREMENT_DIR / "take_gantry.csv"
OPTITRACK_FILE = MEASUREMENT_DIR / "take_optitrack.csv"
CONFIG_FILE = MEASUREMENT_DIR / "config.json"
CALIBRATION_FILE = MEASUREMENT_DIR / "calibration.json"

# RoboLoc-G dataset
DATASET_DIR = SRC_DIR.parents[2] / "roboloc-g-dataset-code/data/roboloc-g"
