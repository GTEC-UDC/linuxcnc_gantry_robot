/********************************************************************
 * calibxyzlib.h
 * Main routines for calibrated kinematics -- header file
 *
 * Authors: LinuxCNC Authors, Tomás D. Bolaño
 * License: GPL Version 2 or later
 *
 * Copyright (C) 2025 LinuxCNC Authors, Tomás D. Bolaño
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, see
 * https://www.gnu.org/licenses/.
 ********************************************************************/

#ifndef CALIBXYZKINSLIB_H
#define CALIBXYZKINSLIB_H

/**
 * Transform joints to position
 * The position is obtained using the following formula:
 *
 * [p_0, p_1, p_2]^T = A * [j_0, j_1, j_2]^T +
 *                     B * [j_0^2, j_1^2, j_2^2]^T +
 *                     C
 *
 * Where p_i and j_i are the ith position and joint coordinates, respectively,
 * and ^T is the transpose operation.
 */
void calib_xyz_forward(const double A[3][3], const double B[3][3],
                       const double C[3], const double joints[3],
                       double position[3]);

/**
 * Transform position to joints
 * The joints values are obtaining by finding the inverse of the
 * transformation used in calib_xyz_kins_forward:
 *
 * [p_0, p_1, p_2]^T = A * [j_0, j_1, j_2]^T +
 *                     B * [j_0^2, j_1^2, j_2^2]^T +
 *                     C
 *
 * Where p_i and j_i are the ith position and joint coordinates, respectively,
 * and ^T is the transpose operation.
 *
 * The joints positions are found using the Newton-Raphson method. The maximum
 * number of iterations and minimum tolerance of the method are controlled with
 * the max_iter and tol parameters, respectively. If min_bounds and max_bounds
 * parameters are not NULL then the obtained joints positions will be within the
 * specified bounds.
 *
 * The Jacobian matrix for this problem is:
 *
 * J = A + 2 * B * diag([j_0, j_1, j_2])
 *
 * To guarantee that the Newton-Raphson method always converges to the expected
 * result within the specified bounds the user should check that J is always
 * invertible within the bounds.
 *
 * Returns -1 if the joints could not be obtained due to the Jacobian
 * being non-invertible, 0 in other case.
 */
int calib_xyz_inverse(const double A[3][3], const double B[3][3],
                      const double C[3], const double *min_bounds,
                      const double *max_bounds, const unsigned int max_iter,
                      const double tol, const double position[3],
                      double joints[3], double *F_norm);

/*
 * Check that inverse exist within min and max bounds for calibration matrices A
 * and B. The result is one of:
 *   *  0: Matrix A is invertible and Jacobian J = A + 2 * B * diag(x) is
 *         invertible for all values x within the bounds.
 *   * -1: det(A) == 0, and thus matrix A is not invertible
 *   * -2: ||2 * A^-1 * B * diag(x)|| >= 1, and thus we cannot assert that the
 *         Jacobian is invertible for all x within the bounds.
 */
int calib_xyz_check_inv(const double A[3][3], const double B[3][3],
                        const double min_bounds[3], const double max_bounds[3]);

#endif