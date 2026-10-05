import argparse
from pathlib import Path

import numpy as np
from data import load_correction_params
from defaults import CALIBRATION_FILE

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

    params = load_correction_params(args.calibration)

    # The calibxyzkins module implements the model up to the second degree, with
    # the matrix A for the linear terms and the matrix B for the squares
    if params.degree > 2:
        parser.error(
            f"The correction model of {args.calibration} is of degree "
            f"{params.degree}, and the calibxyzkins module supports up to degree 2"
        )

    A = np.array(params.A[0])
    B = np.array(params.A[1]) if params.degree == 2 else np.zeros((3, 3))
    c = np.array(params.c)

    coords = ["x", "y", "z"]

    for matrix_name, matrix in (('A', A), ('B', B)):
        print(f"# Calibration matrix {matrix_name}")
        name = matrix_name.lower()

        for row_i, row_coord in enumerate(coords):
            for col_i, col_coord in enumerate(coords):
                param = f"calibxyzkins.calib-{name}.{row_coord}{col_coord}"
                value = matrix[row_i, col_i]
                print(f"setp {param} {value:.10g}")

        print()

    print("# Calibration vector C")
    for row_i, row_coord in enumerate(coords):
        param = f"calibxyzkins.calib-c.{row_coord}"
        value = c[row_i]
        print(f"setp {param} {value:.10g}")
