/********************************************************************
 * linalg3.h
 * Utility routines for 3x3 matrices
 *
 * Author: Tomás D. Bolaño
 * License: GPL Version 2 or later
 *
 * Copyright (C) 2025 Tomás D. Bolaño
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
#include <stdio.h>

#include "linalg3.h"

void print_m_3x3(const double m[3][3]) { fprint_m_3x3(stdin, m); }

void fprint_m_3x3(FILE *stream, const double m[3][3]) {
  fprintf_m_3x3(stream, " 10.3g", m);
}

void fprintf_m_3x3(FILE *stream, const char *fmt, const double m[3][3]) {
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      fprintf(stream, fmt, m[i][j]);
    }
    fprintf(stream, "\n");
  }
}

/*
 * (i,j) minor of a 3x3 matrix
 */
static double minor_m_3x3(int i, int j, const double m[3][3]) {
  return m[i == 0][j == 0] * m[2 - (i == 2)][2 - (j == 2)] -
         m[i == 0][2 - (j == 2)] * m[2 - (i == 2)][j == 0];
}

/*
 * Determinant of a 3x3 matrix
 */
double det_m_3x3(const double m[3][3]) {
  return m[0][0] * minor_m_3x3(0, 0, m) - m[0][1] * minor_m_3x3(0, 1, m) +
         m[0][2] * minor_m_3x3(0, 2, m);
}

int inv_m_3x3(const double m[restrict 3][3], double inverse[restrict 3][3]) {
  double det = det_m_3x3(m);

  if (det == 0.0) {
    return -EINVAL;
  }

  // Calculate Inverse by dividing the transpose cofactors by the determinant
  inverse[0][0] = minor_m_3x3(0, 0, m) / det;
  inverse[1][0] = -minor_m_3x3(0, 1, m) / det;
  inverse[2][0] = minor_m_3x3(0, 2, m) / det;
  inverse[0][1] = -minor_m_3x3(1, 0, m) / det;
  inverse[1][1] = minor_m_3x3(1, 1, m) / det;
  inverse[2][1] = -minor_m_3x3(1, 2, m) / det;
  inverse[0][2] = minor_m_3x3(2, 0, m) / det;
  inverse[1][2] = -minor_m_3x3(2, 1, m) / det;
  inverse[2][2] = minor_m_3x3(2, 2, m) / det;

  return 0;
}

void mult_mm_3x3(const double m1[3][3], const double m2[3][3],
                 double result[restrict 3][3]) {
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      result[i][j] = 0;
      for (int k = 0; k < 3; ++k) {
        result[i][j] += m1[i][k] * m2[k][j];
      }
    }
  }
}

void mult_mv_3x3(const double m1[3][3], const double v[3],
                 double result[restrict 3]) {
  for (int i = 0; i < 3; ++i) {
    result[i] = 0;
    for (int j = 0; j < 3; ++j) {
      result[i] += m1[i][j] * v[j];
    }
  }
}

void sum_vv_3(const double v1[3], const double v2[3],
              double result[restrict 3]) {
  for (int i = 0; i < 3; ++i) {
    result[i] = v1[i] + v2[i];
  }
}

double norm_1_m_3x3(const double m[3][3]) {
  double norm = 0;

  for (int i = 0; i < 3; ++i) {
    double abs_sum = 0;
    for (int j = 0; j < 3; ++j) {
      abs_sum += fabs(m[j][i]);
    }
    norm = abs_sum > norm ? abs_sum : norm;
  }

  return norm;
}

double norm_inf_m_3x3(const double m[3][3]) {
  double norm = 0;

  for (int i = 0; i < 3; ++i) {
    double abs_sum = 0;
    for (int j = 0; j < 3; ++j) {
      abs_sum += fabs(m[i][j]);
    }
    norm = abs_sum > norm ? abs_sum : norm;
  }

  return norm;
}