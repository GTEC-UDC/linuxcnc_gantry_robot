/********************************************************************
 * calibxyzkinslib.h
 * Main routines for calibrated kinematics
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

#include <errno.h>
#include <math.h>
#include <stdbool.h>

#include "calibxyzlib.h"
#include "linalg3.h"

void calib_xyz_forward(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                       const double c[3], const double joints[3],
                       double position[3]) {
  double acc[3][3];

  // position = c + sum_{k=0}^{n-1} A[k] * joints^(k+1)
  //
  // Using Horner's method:
  //
  // acc[i][j] = A[0][i][j] +
  //             A[1][i][j] * joints[j] +
  //             ... +
  //             A[degree-1][i][j] * joints[j]^(degree-1)

  // Initialize acc with case k = degree - 1
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      acc[i][j] = A[degree - 1][i][j];
    }
  }

  // Loop for k < degree - 1. If degree = 1 this does nothing.
  for (int k = degree - 2; k >= 0; --k) {
    for (int i = 0; i < 3; ++i) {
      for (int j = 0; j < 3; ++j) {
        acc[i][j] = acc[i][j] * joints[j] + A[k][i][j];
      }
    }
  }

  // Note that acc[i][j] is missing a joints[j] power
  // so here we multiply acc[i][j] by joints[j]
  for (int i = 0; i < 3; ++i) {
    position[i] = c[i];
    for (int j = 0; j < 3; ++j) {
      position[i] += acc[i][j] * joints[j];
    }
  }
}

/*
 * Calculate the Jacobian matrix:
 * J = sum_{k=0}^{n-1} (k+1) * A[k] * diag(joints)^k
 */
static void jacobian(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                     const double joints[3], double jacobian[3][3]) {
  // Using Horner's method:
  //
  // jacobian[i][j] = A[0][i][j] +
  //                  2 * A[1][i][j] * joints[j] +
  //                  ... +
  //                  degree * A[degree-1][i][j] * joints[j]^(degree-1)

  // Initialize acc with case k = degree - 1
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      jacobian[i][j] = degree * A[degree - 1][i][j];
    }
  }

  // Loop for k < degree - 1. If degree = 1 this does nothing.
  for (int k = degree - 2; k >= 0; --k) {
    for (int i = 0; i < 3; ++i) {
      for (int j = 0; j < 3; ++j) {
        jacobian[i][j] = jacobian[i][j] * joints[j] + (k + 1) * A[k][i][j];
      }
    }
  }
}

static double clamp(double val, double min, double max) {
  const double t = val < min ? min : val;
  return t > max ? max : t;
}

int calib_xyz_inverse(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                      const double c[3], const double *min_bounds,
                      const double *max_bounds, unsigned int max_iter,
                      const double tol, const double position[3],
                      double joints[3], double *r_norm) {
  double r_norm_val = 0;
  double r[3];
  double J[3][3];
  double inv_J[3][3];
  double delta[3];

  bool bound_result = min_bounds != NULL && max_bounds != NULL;

  if (bound_result) {
    // Initialize joints to position or closest bound
    for (int i = 0; i < 3; ++i) {
      joints[i] = clamp(position[i], min_bounds[i], max_bounds[i]);
    }
  } else {
    // Initialize joints to position
    for (int i = 0; i < 3; ++i) {
      joints[i] = position[i];
    }
  }

  for (int iter = 0; iter < max_iter; ++iter) {

    // r = c + sum_{k=0}^{n-1} A[k] * joints^(k+1) - position
    calib_xyz_forward(degree, A, c, joints, r);

    for (int i = 0; i < 3; ++i) {
      r[i] -= position[i];
    }

    // Euclidean norm of r
    r_norm_val = sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);

#ifdef CALIB_XYZ_INVERSE_PRINT_ITER
    printf("Iteration %d r = %5.4g, %5.4g, %5.4g\n", iter, r[0], r[1], r[2]);
    printf("Iteration %d joints = %5.4g, %5.4g, %5.4g\n", iter, joints[0],
           joints[1], joints[2]);
    printf("Iteration %d r_norm = %8.4g\n", iter, r_norm_val);
#endif

    if (r_norm_val < tol) {
      break;
    }

    // Jacobian J = sum_{k=0}^{n-1} (k+1) * A[k] diag(joints)^k
    jacobian(degree, A, joints, J);

    // Inverse of Jacobian
    if (inv_m_3x3(J, inv_J)) {
      return -1;
    }

    // delta = J^-1 * r
    mult_mv_3x3(inv_J, r, delta);

    // Update joints
    if (bound_result) {
      for (int i = 0; i < 3; ++i) {
        joints[i] = clamp(joints[i] - delta[i], min_bounds[i], max_bounds[i]);
      }
    } else {
      for (int i = 0; i < 3; ++i) {
        joints[i] = joints[i] - delta[i];
      }
    }
  }

  if (r_norm != NULL) {
    *r_norm = r_norm_val;
  }

  return 0;
}

// a * b with the convention 0 * inf = 0
static double mul0(double a, double b) { return a == 0.0 ? 0.0 : a * b; }

int calib_xyz_check_inv(int degree, const double A[CALIB_XYZ_MAX_DEGREE][3][3],
                        const double min_bounds[3],
                        const double max_bounds[3]) {
  double inv_A0[3][3];
  double max_abs_bounds[3];
  double T[3][3];
  double M[3][3];

  if (inv_m_3x3(A[0], inv_A0)) {
    return -1;
  }

  if (degree == 1) {
    // For degree 1 the model only needs for A to have inverse
    return 0;
  }

  // Max absolute value of bounds
  for (int i = 0; i < 3; ++i) {
    if (isnan(min_bounds[i]) || isnan(max_bounds[i])) {
      return -EINVAL;
    }
    double min_abs = fabs(min_bounds[i]);
    double max_abs = fabs(max_bounds[i]);
    max_abs_bounds[i] = min_abs > max_abs ? min_abs : max_abs;
  }

  // Calculate matrix
  // M = sum_{k=1}^{n-1} (k+1) * | A[0]^-1 * A[k] | * diag(max_abs_bounds)^k
  //
  // Using Horner's method:
  // With M[k] = A[0]^-1 * A[k]
  //
  // T[i][j] = 2 * |M[1][i][j]| * max_abs_bounds[j] +
  //           3 * |M[2][i][j]| * max_abs_bounds[j]^2 +
  //           ... +
  //           degree * |M[degree-1][i][j]| * max_abs_bounds[j]^(degree-1)

  // Initialize T with case k = degree - 1
  mult_mm_3x3(inv_A0, A[degree - 1], M);
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      T[i][j] = degree * fabs(M[i][j]);
    }
  }

  // Loop for k < degree - 1 until k == 1. If degree = 2 this does nothing.
  for (int k = degree - 2; k >= 1; --k) {
    mult_mm_3x3(inv_A0, A[k], M);
    for (int i = 0; i < 3; ++i) {
      for (int j = 0; j < 3; ++j) {
        T[i][j] = mul0(T[i][j], max_abs_bounds[j]) + (k + 1) * fabs(M[i][j]);
      }
    }
  }

  // Note that T[i][j] is missing a max_abs_bounds[j] power
  // so here we multiply T[i][j] by max_abs_bounds[j]
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      T[i][j] = mul0(T[i][j], max_abs_bounds[j]);
      if (!isfinite(T[i][j])) {
        return -2;
      }
    }
  }

  if (norm_1_m_3x3(T) < 1 || norm_inf_m_3x3(T) < 1) {
    return 0;
  }

  return -2;
}