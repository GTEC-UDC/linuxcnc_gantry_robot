/********************************************************************
 * linalg3.h
 * Utility routines for 3x3 matrices -- header file
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

#ifndef LINALG3_H
#define LINALG3_H

#include <stdio.h>

/*
 * Print 3x3 matrix. Each entry is printed with the format 10.3g.
 */
void print_m_3x3(const double m[3][3]);

/*
 * Print 3x3 matrix to stream. Each entry is printed with the format 10.3g.
 */
void fprint_m_3x3(FILE *stream, const double m[3][3]);

/*
 * Print 3x3 matrix to stream with an specific format for each entry
 */
void fprintf_m_3x3(FILE *stream, const char *fmt, const double m[3][3]);

/*
 * Determinant of a 3x3 matrix
 */
double det_m_3x3(const double m[3][3]);

/**
 * Inverse of a 3x3 matrix
 */
int inv_m_3x3(const double m[restrict 3][3], double inv[restrict 3][3]);

/**
 * Multiply two 3x3 matrices
 */
void mult_mm_3x3(const double m1[3][3], const double m2[3][3],
                 double result[restrict 3][3]);

/**
 * Multiply 3x3 matrix by 3x1 vector
 */
void mult_mv_3x3(const double m[3][3], const double v[3],
                 double result[restrict 3]);

/**
 * Sum two vectos of 3 elements
 */
void sum_vv_3(const double v1[3], const double v2[3],
              double result[restrict 3]);

/**
 * 1-norm of 3x3 matrix
 */
double norm_1_m_3x3(const double m[3][3]);

/**
 * inf norm of 3x3 matrix
 */
double norm_inf_m_3x3(const double m[3][3]);

#endif // LINALG3_H
