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

void calib_xyz_forward(const double A[3][3], const double B[3][3],
                       const double c[3], const double joints[3],
                       double position[3]) {
  for (int i = 0; i < 3; ++i) {
    position[i] = c[i];
    for (int j = 0; j < 3; ++j) {
      position[i] += A[i][j] * joints[j] + B[i][j] * joints[j] * joints[j];
    }
  }
}

static double clamp(double val, double min, double max) {
  const double t = val < min ? min : val;
  return t > max ? max : t;
}

int calib_xyz_inverse(const double A[3][3], const double B[3][3],
                      const double c[3], const double *min_bounds,
                      const double *max_bounds, const unsigned int max_iter,
                      const double tol, const double position[3],
                      double joints[3], double *r_norm) {
  double r[3];
  double r_norm_val;
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
    // r = A * joints + B * joints^2 + c - position
    for (int i = 0; i < 3; ++i) {
      r[i] = c[i] - position[i];
      for (int j = 0; j < 3; ++j) {
        r[i] += A[i][j] * joints[j] + B[i][j] * joints[j] * joints[j];
      }
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

    // Jacobian J = A + 2 * B * diag(joints)
    for (int i = 0; i < 3; ++i) {
      for (int j = 0; j < 3; ++j) {
        J[i][j] = A[i][j] + 2 * B[i][j] * joints[j];
      }
    }

    // Inverse of Jacobian
    if (inv_m_3x3(J, inv_J)) {
      return -EINVAL;
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

int calib_xyz_check_inv(const double A[3][3], const double B[3][3],
                        const double min_bounds[3],
                        const double max_bounds[3]) {
  double inv_A[3][3];
  double max_abs_bounds[3];
  double M[3][3];

  if (inv_m_3x3(A, inv_A)) {
    return -1;
  }

  // Max absolute value of bounds
  for (int i = 0; i < 3; ++i) {
    double min_abs = fabs(min_bounds[i]);
    double max_abs = fabs(max_bounds[i]);
    max_abs_bounds[i] = min_abs > max_abs ? min_abs : max_abs;
  }

  // M = 2 * A^-1 * B * diag(max_abs_bounds)
  mult_mm_3x3(inv_A, B, M);

  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      M[i][j] = 2 * M[i][j] * max_abs_bounds[j];
    }
  }

  if (norm_1_m_3x3(M) >= 1 || norm_inf_m_3x3(M) >= 1) {
    return -2;
  }

  return 0;
}