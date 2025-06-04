/********************************************************************
 * calibxyzkins.h
 * Calibrated XYZ kinematics for cartesian machines
 * Derived from trivkins.c
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

/*-------------------------------------------------------------------
This module provides forward and inverse kinematic functions for a calibrated
XYZ cartesian machine. The forward transformation from joints jx, jy, jz
to positions x, y, z is defined as:

[x, y, z]^T = A * [jx, jy, jz]^T + B * [jx^2, jy^2, jz^2]^T + C

Where A and B are 3x3 matrices, C is a 3x1 vector, and ^T is the transpose
operation.

The default values for A, B, and C are:
  - A: 3x3 identity matrix
  - B: all zero 3x3 matrix
  - C: all zero 3x1 matrix

Thus, by default the kinematics are just the trivial kinematics.

The inverse transformation is obtained using the Newton-Raphson method.
The maximum number of iterations and tolerance of the method can be set with the
provided HAL pins.

HAL parameters (defaults in parentheses):
  * Calibration matrix A:
    calibxyzkins.calib-a.xx (1)
    calibxyzkins.calib-a.xy (0)
    calibxyzkins.calib-a.xz (0)
    calibxyzkins.calib-a.yx (0)
    calibxyzkins.calib-a.yy (1)
    calibxyzkins.calib-a.yz (0)
    calibxyzkins.calib-a.zx (0)
    calibxyzkins.calib-a.zy (0)
    calibxyzkins.calib-a.zz (1)

  * Calibration matrix B:
    calibxyzkins.calib-b.xx (0)
    calibxyzkins.calib-b.xy (0)
    calibxyzkins.calib-b.xz (0)
    calibxyzkins.calib-b.yx (0)
    calibxyzkins.calib-b.yy (0)
    calibxyzkins.calib-b.yz (0)
    calibxyzkins.calib-b.zx (0)
    calibxyzkins.calib-b.zy (0)
    calibxyzkins.calib-b.zz (0)

  * Calibration vector C:
    calibxyzkins.calib-c.xx (0)
    calibxyzkins.calib-c.xy (0)
    calibxyzkins.calib-c.xz (0)

  * Max/min joints limits for the XYZ axes:
    calibxyzkins.min-limit.x (-inf)
    calibxyzkins.min-limit.y (-inf)
    calibxyzkins.min-limit.z (-inf)

    calibxyzkins.max-limit.x (inf)
    calibxyzkins.max-limit.y (inf)
    calibxyzkins.max-limit.z (inf)

HAL pins (defaults in parentheses):
  calibxyzkins.max-iter (10) -- Maximum number of iterations for the
                                inverse kinematics
  calibxyzkins.tol (1e-3) -- Tolerance for the inverse kinematics

---------------------------------------------------------------------*/

#include <errno.h>

#include "hal.h"
#include "kinematics.h"
#include "rtapi.h"     /* RTAPI realtime OS API */
#include "rtapi_app.h" /* RTAPI realtime module decls */

#include "calibxyzkinsutils.h"

// Module information
MODULE_DESCRIPTION("Calibrated XYZ kinematics for cartesian machines")
MODULE_AUTHOR("LinuxCNC Authors, Tomás D. Bolaño")
MODULE_LICENSE("GPL")

// System coordinates input parameter
static const char *coordinates = "XYZABCUVW";
RTAPI_MP_STRING(coordinates, "Existing Axes")

/*
 * Global data
 */
static joints_mapping_t joints_mapping;
static haldata_t *haldata;
static bool calib_xyz_initialized = false;
static int comp_id;

/*
 * Update position from joints based on the mapping created by
 * map_coordinates_to_jnumbers().
 */
int kinematicsForward(const double *joints, EmcPose *pos,
                      const KINEMATICS_FORWARD_FLAGS *fflags,
                      KINEMATICS_INVERSE_FLAGS *iflags) {
  if (!calib_xyz_initialized) {
    rtapi_print_msg(RTAPI_MSG_ERR, "calibxyzkins: not initialized\n");
    return -EPERM;
  }

  return calib_xyz_kins_forward(&joints_mapping, haldata, joints, pos);
}

/*
 * Update joints (including joints for duplicate letters)
 * based on the mapping created by map_coordinates_to_jnumbers().
 */
int kinematicsInverse(const EmcPose *pos, double *joints,
                      const KINEMATICS_INVERSE_FLAGS *iflags,
                      KINEMATICS_FORWARD_FLAGS *fflags) {
  if (!calib_xyz_initialized) {
    rtapi_print_msg(RTAPI_MSG_ERR, "calibxyzkins: not initialized\n");
    return -EPERM;
  }

  return calib_xyz_kins_inverse(&joints_mapping, haldata, pos, joints);
}

KINEMATICS_TYPE
kinematicsType() { return KINEMATICS_BOTH; }

KINS_NOT_SWITCHABLE
EXPORT_SYMBOL(kinematicsType)
EXPORT_SYMBOL(kinematicsForward)
EXPORT_SYMBOL(kinematicsInverse)

int rtapi_app_main(void) {
  int res = 0;
  comp_id = hal_init("calibxyzkins");

  if (comp_id < 0) {
    rtapi_print_msg(RTAPI_MSG_ERR, "calibxyzkins: hal_init failed\n");
    return comp_id;
  }

  rtapi_print_msg(RTAPI_MSG_ERR, "calibxyzkins: setting up\n");
  if ((res = calib_xyz_kins_setup(comp_id, coordinates, EMCMOT_MAX_JOINTS, true,
                                  &haldata, &joints_mapping)) < 0) {
    hal_exit(comp_id);
    return res;
  }

  calib_xyz_initialized = true;

  hal_ready(comp_id);
  rtapi_print_msg(RTAPI_MSG_ERR, "calibxyzkins: ready\n");

  return 0;
}

void rtapi_app_exit(void) { hal_exit(comp_id); }
