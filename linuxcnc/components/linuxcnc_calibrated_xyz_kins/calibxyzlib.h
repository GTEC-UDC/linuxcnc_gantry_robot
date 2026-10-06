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

#define CALIB_XYZ_MAX_DEGREE 5

/**
 * Transform joints jx, jy, jz to position x, y, z using the following
 * formula:
 *
 * [x, y, z]^T = c + sum_{k=1}^{n} A_k * [jx^k, jy^k, jz^k]^T
 *
 * Where n is the degree of the transformation, c is a 3x1 vector, the
 * A_k are 3x3 matrices, and ^T is the transpose operation.
 *
 * Returns the position in the position parameter
 */
void calib_xyz_forward(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                       const double c[3], const double joints[3],
                       double position[3]);

/**
 * Transform position x, y, z to joints jx, jy, jz by finding the
 * inverse of the transformation used in calib_xyz_kins_forward:
 *
 * [x, y, z]^T = c + sum_{k=1}^{n} A_k * [jx^k, jy^k, jz^k]^T
 *
 * Where n is the degree of the transformation, c is a 3x1 vector, the
 * A_k are 3x3 matrices, and ^T is the transpose operation.
 *
 * The joints positions are found using the Newton-Raphson method. The
 * maximum number of iterations and minimum tolerance of the method are
 * controlled with the max_iter and tol parameters, respectively. If
 * min_bounds and max_bounds parameters are not NULL then the obtained
 * joints positions will be within the specified bounds.
 *
 * The Jacobian matrix for this problem is:
 *
 * J = sum_{k=1}^{n} k * A_k diag([jx, jy, jz])^(k - 1)
 *
 * To guarantee that the Newton-Raphson method always converges to the
 * expected result within the specified bounds the user should check
 * that J is always invertible within the bounds.
 *
 * Returns -1 if the joints could not be obtained due to the Jacobian
 * being non-invertible, 0 in other case.
 */
int calib_xyz_inverse(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                      const double c[3], const double *min_bounds,
                      const double *max_bounds, unsigned int max_iter,
                      const double tol, const double position[3],
                      double joints[3], double *r_norm);

/*
 * Check that inverse exist within min and max bounds for calibration
 * matrices A_k. The result is one of:
 *   *  -EINVAL: min_bounds or max_bounds contain NaN values.
 *   *  0: Matrix A is invertible and Jacobian is invertible for all
 *         values x within the bounds.
 *   * -1: det(A_1) == 0, and thus matrix A_1 is not invertible
 *   * -2: || sum_{k=2}^{n} k |A_1^-1 * A_k| * diag(x)^(k-1) || >= 1,
 *         and thus we cannot assert that the Jacobian is invertible
 *         for all x within the bounds.
 */
int calib_xyz_check_inv(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                        const double min_bounds[3], const double max_bounds[3]);

#endif