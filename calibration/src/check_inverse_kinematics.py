"""Convergence of the inverse kinematics solver over the workspace.

This script runs the Newton-Raphson iteration of the `calibxyzkins` module on a grid
of target axis positions and reports how far the initial estimate is from the
solution, how many steps the iteration needs, and the residual it leaves.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import numpy.typing as npt
from data import PolynomialCorrection, load_correction
from defaults import CALIBRATION_FILE

Bounds = tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]

# Iterations used to compute the reference solution
REFERENCE_ITER = 50


def jacobian(
    correction: PolynomialCorrection, joints: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Jacobian of the correction at each row of ``joints``.

    It is the sum of k * A_k @ diag(x)**(k - 1), for k from 1 to the degree.
    """
    out = np.zeros((joints.shape[0], 3, 3))
    for k, mat in enumerate(np.array(correction.A), start=1):
        out += k * mat * joints[:, None, :] ** (k - 1)
    return out


def newton_step(
    correction: PolynomialCorrection,
    joints: npt.NDArray[np.float64],
    residual: npt.NDArray[np.float64],
    bounds: Bounds | None,
) -> npt.NDArray[np.float64]:
    delta = np.linalg.solve(jacobian(correction, joints), residual[:, :, None])[:, :, 0]
    joints = joints - delta
    if bounds is not None:
        joints = np.clip(joints, bounds[0], bounds[1])
    return joints


def inverse_kinematics(
    pos: npt.NDArray[np.float64],
    correction: PolynomialCorrection,
    bounds: Bounds | None = None,
    max_iter: int = 10,
    tol: float = 1e-3,
) -> tuple[
    npt.NDArray[np.float64],
    npt.NDArray[np.int_],
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
]:
    """Solve the inverse kinematics of each row of ``pos`` as `calibxyzkins` does.

    The joints start at the target position, bounded by the joint limits if given.
    Each iteration evaluates the residual of the correction and stops if its norm is
    below ``tol``; otherwise it takes a Newton-Raphson step.

    Returns the joints, the number of steps taken for each position, the norm of the
    residual left, and the largest norm of the residual at the start of each
    iteration.
    """
    joints = pos.copy()
    if bounds is not None:
        joints = np.clip(joints, bounds[0], bounds[1])

    steps = np.zeros(pos.shape[0], dtype=int)
    r_norm = np.zeros(pos.shape[0])
    active = np.ones(pos.shape[0], dtype=bool)
    worst_r_norm = []

    for _ in range(max_iter):
        residual = correction.apply(joints[active]) - pos[active]
        r_norm[active] = np.linalg.norm(residual, axis=1)
        worst_r_norm.append(r_norm.max())

        not_converged = r_norm[active] >= tol
        active[active] = not_converged
        if not active.any():
            break

        joints[active] = newton_step(
            correction, joints[active], residual[not_converged], bounds
        )
        steps[active] += 1

    return joints, steps, r_norm, np.array(worst_r_norm)


def check_inverse_kinematics(
    correction: PolynomialCorrection,
    axis_bounds: Bounds,
    points: int,
    joint_bounds: Bounds | None = None,
    max_iter: int = 10,
    tol: float = 1e-3,
) -> bool:
    grid = [np.linspace(axis_bounds[0][i], axis_bounds[1][i], points) for i in range(3)]
    pos = np.stack(np.meshgrid(*grid, indexing="ij"), axis=-1).reshape(-1, 3)

    joints, steps, r_norm, worst_r_norm = inverse_kinematics(
        pos, correction, joint_bounds, max_iter, tol
    )
    converged = r_norm < tol

    # Reference solution: unbounded iteration run well past convergence
    reference = pos.copy()
    for _ in range(REFERENCE_ITER):
        residual = correction.apply(reference) - pos
        reference = newton_step(correction, reference, residual, None)

    initial = pos if joint_bounds is None else np.clip(pos, *joint_bounds)
    initial_dist = np.linalg.norm(initial - reference, axis=1)

    print(f"Correction model of degree {correction.degree}")
    print(f"Target positions: {pos.shape[0]} ({points} per axis)")
    print(f"Axis limits: min = {axis_bounds[0]}, max = {axis_bounds[1]}")
    if joint_bounds is not None:
        print(f"Joint limits: min = {joint_bounds[0]}, max = {joint_bounds[1]}")
    print(f"Tolerance: {tol:g} mm, maximum iterations: {max_iter}")

    print("\nDistance from the initial estimate to the solution (mm):")
    print(
        f"  max = {initial_dist.max():.2f}, "
        f"95th percentile = {np.percentile(initial_dist, 95):.2f}, "
        f"median = {np.median(initial_dist):.2f}"
    )
    print(f"  max per joint = {np.abs(initial - reference).max(axis=0).round(2)}")

    print(
        f"\nJoints of the solution: min = {reference.min(axis=0).round(2)}, "
        f"max = {reference.max(axis=0).round(2)}"
    )

    print("\nNewton-Raphson steps needed:")
    for n_steps, count in zip(*np.unique(steps[converged], return_counts=True)):
        print(f"  {n_steps} step(s): {count} positions")
    if not converged.all():
        print(f"  not converged: {np.count_nonzero(~converged)} positions")

    print("\nWorst residual norm at each iteration (mm):")
    for i, value in enumerate(worst_r_norm):
        print(f"  after {i} step(s): {value:.3g}")

    print(f"\nWorst residual norm left: {r_norm.max():.3g} mm")
    print(
        "Worst distance from the joints found to the solution: "
        f"{np.linalg.norm(joints - reference, axis=1).max():.3g} mm"
    )

    return bool(converged.all())


def main():
    parser = argparse.ArgumentParser(
        description="Check the convergence of the inverse kinematics solver",
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
        default=[-5.0, -5.0, -1050.0],
    )

    parser.add_argument(
        "--axis-max",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Maximum values for the X Y Z axis positions",
        type=float,
        default=[5300.0, 5200.0, 5.0],
    )

    parser.add_argument(
        "--joints-min",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Minimum values for the X Y Z joint values (not limited if not given)",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--joints-max",
        nargs=3,
        metavar=("X", "Y", "Z"),
        help="Maximum values for the X Y Z joint values (not limited if not given)",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--points",
        help="Number of target positions per axis",
        type=int,
        default=41,
    )

    parser.add_argument(
        "--max-iter",
        help="Maximum number of iterations of the solver",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--tol",
        help="Tolerance of the solver, in mm",
        type=float,
        default=1e-3,
    )

    args = parser.parse_args()

    if (args.joints_min is None) != (args.joints_max is None):
        parser.error("--joints-min and --joints-max must be given together")

    joint_bounds = None
    if args.joints_min is not None:
        joint_bounds = (np.array(args.joints_min), np.array(args.joints_max))

    correction = load_correction(args.calibration)

    if not check_inverse_kinematics(
        correction,
        (np.array(args.axis_min), np.array(args.axis_max)),
        args.points,
        joint_bounds=joint_bounds,
        max_iter=args.max_iter,
        tol=args.tol,
    ):
        print("\nInverse kinematics test failed. The solver did not converge.")
        sys.exit(1)

    print("\nInverse kinematics test passed. The solver converged at every position.")


if __name__ == "__main__":
    main()
