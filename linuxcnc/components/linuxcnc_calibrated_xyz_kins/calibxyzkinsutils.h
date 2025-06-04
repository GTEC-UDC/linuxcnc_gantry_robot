/********************************************************************
 * calibxyzkins.h
 * Utility routines for calibxyzkins.c -- header file
 * Derived from kins_util.c
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

#ifndef CALIBXYZKINSUTILS_H
#define CALIBXYZKINSUTILS_H

#include "emcmotcfg.h"
#include "emcpos.h"
#include "hal.h"

/*
 * HAL data
 * Parameters:
 *  - Calibration matrices A and B, and vector C
 *  - Min/max values of joints of XYZ coordinates
 * Pins:
 *  - Max iterations for inverse kinematics
 *  - Tolerance for inverse kinematics
 */
typedef struct {
  hal_float_t calib_m_A[3][3];
  hal_float_t calib_m_B[3][3];
  hal_float_t calib_v_C[3];
  hal_float_t joints_min[3];
  hal_float_t joints_max[3];
  hal_u32_t *max_iter;
  hal_float_t *tol;
} haldata_t;

/*
 * Type for joints mapping data
 */
typedef struct {
  // Axis number for joint number:
  // axes letters: x y z a b c u v w
  // axes numbers: 0 1 2 3 4 5 6 7 8
  int axno_for_jno[EMCMOT_MAX_JOINTS];
  // First joint number for axis number
  int first_jno_for_axno[EMCMOT_MAX_AXIS];
} joints_mapping_t;

/*
 * Initialize the HAL data and the joints mappings
 */
int calib_xyz_kins_setup(int comp_id, const char *coordinates,
                         const int max_joints, const int allow_duplicates,
                         haldata_t **haldata, joints_mapping_t *joints_mapping);
/*
 * Update position from joints based on the joints mapping and the calibration
 * data.
 */
int calib_xyz_kins_forward(const joints_mapping_t *joints_mapping,
                           const haldata_t *haldata, const double *joints,
                           EmcPose *pos);

/*
 * Update joints (including joints for duplicate letters) based on the joints
 * mapping and the calibration data.
 */
int calib_xyz_kins_inverse(const joints_mapping_t *joints_mapping,
                           const haldata_t *haldata, const EmcPose *pos,
                           double *joints);

#endif