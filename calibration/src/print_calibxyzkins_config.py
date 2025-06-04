import argparse

import numpy as np

from data import get_calibration_matrices

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print the LinuxCNC hal configuration for the calibxyzkins module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--calibration",
        help="Path to save the calibration parameters file",
        type=str,
        default="calibration_params.npy",
    )

    args = parser.parse_args()

    params = get_calibration_matrices(np.load(args.calibration))

    # Note that we transpose the calibration matrices because the python code
    # uses row coordinate vectors, but the calibxyzkins module uses column
    # coordinate vectors.
    A = params[0].T
    B = params[1].T
    C = params[2].T

    # print(A)
    # print(B)
    # print(C)

    coords = ["x", "y", "z"]

    print("# Calibration matrix A")
    for row_i, row_coord in enumerate(coords):
        for col_i, col_coord in enumerate(coords):
            print(
                f"setp calibxyzkins.calib-a.{row_coord}{col_coord} {A[row_i, col_i]:.10g}"
            )

    print()
    print("# Calibration matrix B")
    for row_i, row_coord in enumerate(coords):
        for col_i, col_coord in enumerate(coords):
            print(
                f"setp calibxyzkins.calib-b.{row_coord}{col_coord} {B[row_i, col_i]:.10g}"
            )

    print()
    print("# Calibration vector C")
    for row_i, row_coord in enumerate(coords):
        print(f"setp calibxyzkins.calib-c.{row_coord} {C[row_i]:.10g}")
