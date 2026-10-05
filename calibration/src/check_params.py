import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import scipy as scp
from data import CorrectionParams, load_correction_params
from defaults import CALIBRATION_FILE

logger = logging.getLogger(__name__)


def forward_kinematics(
    joint_values: np.ndarray, params: CorrectionParams
) -> np.ndarray:
    return params.apply(joint_values)


def inverse_kinematics(
    pos: np.ndarray,
    params: CorrectionParams,
    x0: np.ndarray | None = None,
    bounds: tuple[np.ndarray, np.ndarray] | None = None,
    max_iter: int = 10,
    tol: float = 1e-3,
) -> np.ndarray:
    matrices = np.array(params.A)

    # Function to minimize
    def f_opt(x: np.ndarray) -> np.ndarray:
        return params.apply(x) - pos

    # Jacobian: sum of k * A_k @ diag(x)**(k - 1)
    def J(x: np.ndarray) -> np.ndarray:
        jacobian = np.zeros((3, 3))
        for k, mat in enumerate(matrices, start=1):
            jacobian += k * mat * x ** (k - 1)
        return jacobian

    x = x0 if x0 is not None else pos

    if bounds is not None:
        if np.any(x.T < bounds[0]) or np.any(x.T > bounds[1]):
            logger.warning(f"Initial x is out of bounds: {x.T}")
        x = np.clip(x.T, bounds[0], bounds[1]).T

    for i in range(max_iter):
        try:
            J_inv = np.linalg.inv(J(x))
        except np.linalg.LinAlgError:
            logger.error(f"J is singular at x = {x}")
            break

        x_new = x - J_inv @ f_opt(x)
        tol_i = np.linalg.norm(x_new - x)

        if bounds is not None:
            x_new = np.clip(x_new.T, bounds[0], bounds[1]).T

        x = x_new

        logger.info(f"inverse_kinematics iter {i}: tol: {tol_i} x: {x}")

        if tol_i < tol:
            break

    return x


def check_J_inv(
    bounds: tuple[np.ndarray, np.ndarray],
    params: CorrectionParams,
) -> bool:
    matrices = np.array(params.A)
    max_abs_x = np.max(np.abs(np.array([bounds[0], bounds[1]])), axis=0)

    # Bound of the entries of the matrix
    # inv(A_1) @ sum of k * A_k @ diag(x)**(k - 1), for k from 2 to the degree
    inv_a1 = np.linalg.inv(matrices[0])
    D = np.zeros((3, 3))
    for k, mat in enumerate(matrices[1:], start=2):
        D += k * np.abs(inv_a1 @ mat) * max_abs_x ** (k - 1)

    norm_1 = np.linalg.norm(D, 1)
    norm_inf = np.linalg.norm(D, np.inf)

    print(f"Jacobian invertibility test: norm 1 = {norm_1} < 1 -> {norm_1 < 1}")
    print(f"Jacobian invertibility test: norm inf = {norm_inf} < 1 -> {norm_inf < 1}")

    return bool(norm_1 < 1 or norm_inf < 1)


def get_joint_bounds(
    params: CorrectionParams,
    axis_bounds: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    min_joints = np.zeros(3)
    max_joints = np.zeros(3)

    # Function to minimize
    def f_opt(pos: np.ndarray, j_idx: int, opt_factor: int) -> float:
        joints = inverse_kinematics(pos, params, max_iter=20, tol=1e-9)
        return joints[j_idx] * opt_factor

    for j_idx in range(3):
        for opt_idx, opt_factor in enumerate([1, -1]):  # Minimize and maximize
            logger.info(f"Finding joint {j_idx} {'min' if opt_idx == 0 else 'max'}...")

            res = scp.optimize.minimize(
                fun=f_opt,
                x0=axis_bounds[0] if opt_idx == 0 else axis_bounds[1],
                args=(j_idx, opt_factor),
                bounds=[(axis_bounds[0][i], axis_bounds[1][i]) for i in range(3)],
                callback=lambda intermediate_result: logger.info(
                    "fval: %s", intermediate_result.fun
                ),
            )

            print(
                f"Found joint {j_idx} {'min' if opt_idx == 0 else 'max'}: "
                f"{res.fun * opt_factor} on axis position {res.x}"
            )

            if opt_idx == 0:
                min_joints[j_idx] = res.fun * opt_factor
            else:
                max_joints[j_idx] = res.fun * opt_factor

    return min_joints, max_joints


def check_joint_bounds(
    params: CorrectionParams,
    axis_bounds: tuple[np.ndarray, np.ndarray],
    joint_bounds: tuple[np.ndarray, np.ndarray],
) -> bool:
    min_joints, max_joints = get_joint_bounds(params, axis_bounds)
    print(f"Joint bounds: min = {min_joints}, max = {max_joints}")

    return bool(
        np.all(joint_bounds[0] <= min_joints) and np.all(max_joints <= joint_bounds[1])
    )


def main():
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        description="Check calibration parameters",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--calibration",
        help="Path to the calibration parameters file",
        type=Path,
        default=CALIBRATION_FILE,
    )

    parser.add_argument(
        "--axis-min",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Minimum values for the X Y Z axis positions",
        type=float,
        default=[0.0, 0.0, -1000.0],
    )

    parser.add_argument(
        "--axis-max",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Maximum values for the X Y Z axis positions",
        type=float,
        default=[5300.0, 5200.0, 0.0],
    )

    parser.add_argument(
        "--joints-min",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Minimum values for the X Y Z joint values",
        type=float,
        default=[-20.0, -20.0, -1020.0],
    )

    parser.add_argument(
        "--joints-max",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Maximum values for the X Y Z joint values",
        type=float,
        default=[5320.0, 5220.0, 20.0],
    )

    args = parser.parse_args()

    params = load_correction_params(args.calibration)

    # Check J invertibility on the joint space
    if not check_J_inv(
        bounds=(np.array(args.joints_min), np.array(args.joints_max)),
        params=params,
    ):
        print(
            "Jacobian invertibility test failed. "
            "Jacobian may be non-invertible on the joint space."
        )
        sys.exit(1)

    print(
        "Jacobian invertibility test passed. Jacobian is invertible on the joint space."
    )

    # Check inverse kinematics from axis to joint space is within the joint limits
    if not check_joint_bounds(
        params,
        (np.array(args.axis_min), np.array(args.axis_max)),
        (np.array(args.joints_min), np.array(args.joints_max)),
    ):
        print("Joint bounds test failed. Inverse kinematics is out of joint limits.")
        sys.exit(1)

    print("Joint bounds test passed. Inverse kinematics is within joint limits.")


if __name__ == "__main__":
    main()
