import argparse

from data import CalibrationParams, get_calibration_matrices

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print the LinuxCNC hal configuration for the calibxyzkins module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--calibration",
        help="Path to save the calibration parameters file",
        type=str,
        default="calibration.json",
    )

    args = parser.parse_args()

    with open(args.calibration, "r") as f:
        calibration_params = CalibrationParams.model_validate_json(f.read())

    params = get_calibration_matrices(calibration_params.correction)

    # Note that we transpose the calibration matrices because the python code
    # uses row coordinate vectors, but the calibxyzkins module uses column
    # coordinate vectors.
    A = params[0].T
    B = params[1].T
    c = params[2].T

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
