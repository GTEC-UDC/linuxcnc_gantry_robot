import argparse
from pathlib import Path

from data import load_correction
from defaults import CALIBRATION_FILE

# Maximum degree of the model in the calibxyzkins module, set at compile time
# with the CALIB_XYZ_MAX_DEGREE macro of calibxyzlib.h
CALIBXYZKINS_MAX_DEGREE = 5

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print the LinuxCNC hal configuration for the calibxyzkins module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--calibration",
        help="Path to save the calibration parameters file",
        type=Path,
        default=CALIBRATION_FILE,
    )

    args = parser.parse_args()

    correction = load_correction(args.calibration)

    if correction.degree > CALIBXYZKINS_MAX_DEGREE:
        parser.error(
            f"The correction model of {args.calibration} is of degree "
            f"{correction.degree}, and the calibxyzkins module supports up to degree "
            f"{CALIBXYZKINS_MAX_DEGREE}"
        )

    coords = ["x", "y", "z"]

    # The module creates the parameters of the matrices A1 to An, with n the
    # value of its degree parameter
    print(f"# Load the calibxyzkins module with degree={correction.degree}")
    print()

    for k, matrix in enumerate(correction.A, start=1):
        print(f"# Calibration matrix A{k}")

        for row_i, row_coord in enumerate(coords):
            for col_i, col_coord in enumerate(coords):
                param = f"calibxyzkins.calib-a{k}.{row_coord}{col_coord}"
                value = matrix[row_i][col_i]
                print(f"setp {param} {value:.10g}")

        print()

    print("# Calibration vector c")
    for row_i, row_coord in enumerate(coords):
        param = f"calibxyzkins.calib-c.{row_coord}"
        value = correction.c[row_i]
        print(f"setp {param} {value:.10g}")
