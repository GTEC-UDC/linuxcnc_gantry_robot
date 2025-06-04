/********************************************************************
 * calibxyzkins.h
 * Utility routines for calibxyzkins.c
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

#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "emcmotcfg.h"
#include "hal.h"
#include "kinematics.h"
#include "motion.h"
#include "rtapi.h"
#include "usrmotintf.h"

#include "calibxyzkinsutils.h"
#include "calibxyzlib.h"

#define MAX_COORDINATES_CHARS 32

/**
 * Map a string of coordinate letters to joint numbers sequentially.
 * If allow_duplicates==1, a coordinate letter may be specified more
 * than once to assign it to multiple joint numbers.
 * Function derived from map_coordinates_to_jnumbers.
 *
 *   Default mapping if coordinates==NULL is:
 *           X:0 Y:1 Z:2 A:3 B:4 C:5 U:6 V:7 W:8
 *
 *   Example coordinates-to-joints mappings:
 *      coordinates=XYZ      X:0   Y:1   Z:2
 *      coordinates=ZYX      Z:0   Y:1   X:2
 *      coordinates=XYZZZZ   x:0   Y:1   Z:2,3,4,5
 *      coordinates=XXYZ     X:0,1 Y:2   Z:3
 */
static int init_joints_mapping(const char *coordinates, const int max_joints,
                               const int allow_duplicates,
                               joints_mapping_t *jmap) {
  const char *errtag = "calibxyzkins";
  const char *coord_letter = "XYZABCUVW";
  int dups[EMCMOT_MAX_AXIS] = {0};
  int jno = 0;
  bool found = 0;

  if (coordinates == NULL) {
    rtapi_print_msg(RTAPI_MSG_ERR, "%s: null coordinates\n", errtag);
    return -EINVAL;
  }

  if (strlen(coordinates) > MAX_COORDINATES_CHARS) {
    rtapi_print_msg(RTAPI_MSG_ERR, "%s: too many chars: %s\n", errtag,
                    coordinates);
    return -EINVAL;
  }

  if ((max_joints <= 0) || (max_joints > EMCMOT_MAX_JOINTS)) {
    rtapi_print_msg(RTAPI_MSG_ERR, "%s: bogus max_joints=%d\n", errtag,
                    max_joints);
    return -EINVAL;
  }

  // init all axis_idx_for_jno[] to -1 (unspecified)
  for (jno = 0; jno < EMCMOT_MAX_JOINTS; jno++) {
    jmap->axno_for_jno[jno] = -1;
  }

  jno = 0; // begin: assign joint numbers at 0th coords position
  for (int i = 0; coordinates[i] != 0; ++i, ++jno) {
    found = 0;
    // clang-format off
    switch (coordinates[i]) {
      case 'x': case 'X': jmap->axno_for_jno[jno] = 0; dups[0]++; found = 1; break;
      case 'y': case 'Y': jmap->axno_for_jno[jno] = 1; dups[1]++; found = 1; break;
      case 'z': case 'Z': jmap->axno_for_jno[jno] = 2; dups[2]++; found = 1; break;
      case 'a': case 'A': jmap->axno_for_jno[jno] = 3; dups[3]++; found = 1; break;
      case 'b': case 'B': jmap->axno_for_jno[jno] = 4; dups[4]++; found = 1; break;
      case 'c': case 'C': jmap->axno_for_jno[jno] = 5; dups[5]++; found = 1; break;
      case 'u': case 'U': jmap->axno_for_jno[jno] = 6; dups[6]++; found = 1; break;
      case 'v': case 'V': jmap->axno_for_jno[jno] = 7; dups[7]++; found = 1; break;
      case 'w': case 'W': jmap->axno_for_jno[jno] = 8; dups[8]++; found = 1; break;
      case ' ': case '\t': continue;  // whitespace
    }
    // clang-format on

    if (!found) {
      rtapi_print_msg(RTAPI_MSG_ERR,
                      "%s: Invalid character '%c' in coordinates '%s'\n",
                      errtag, coordinates[i], coordinates);
      return -EINVAL;
    }

    if (jno > max_joints) {
      rtapi_print_msg(RTAPI_MSG_ERR,
                      "%s: too many coordinates (%s) for max_joints=%d\n",
                      errtag, coordinates, max_joints);
      return -EINVAL;
    }
  }

  if (!found) {
    rtapi_print_msg(RTAPI_MSG_ERR, "%s: missing coordinates '%s'\n", errtag,
                    coordinates);
    return -EINVAL;
  }

  if (!allow_duplicates) {
    for (int axno = 0; axno < EMCMOT_MAX_AXIS; axno++) {
      if (dups[axno] > 1) {
        rtapi_print_msg(
            RTAPI_MSG_ERR,
            "%s: duplicates not allowed in coordinates=%s, letter=%c\n", errtag,
            coordinates, coord_letter[axno]);
        return -EINVAL;
      }
    }
  }

  /*
   * Assign principal joint (first joint listed for a coordinate letter
   * (using the coordinates module parameter).
   *
   * example: coordinates=xyzbcwy (duplicate y)
   *          JX=0 joints: 0
   *          JY=1 joints: 1 and 6
   *          JZ=2 joints: 2
   *          JB=3 joints: 3
   *          JC=4 joints: 4
   *          JW=5 joints: 5
   *
   * axes letters: x y z a b c u v w
   * axes indices: 0 1 2 3 4 5 6 7 8
   */
  for (int axno = 0; axno < EMCMOT_MAX_AXIS; ++axno) {
    jmap->first_jno_for_axno[axno] = -1;
  }

  for (int jno = 0; jno < EMCMOT_MAX_JOINTS; jno++) {
    int axno = jmap->axno_for_jno[jno];
    if (axno == -1) {
      break;
    }
    if (jmap->first_jno_for_axno[axno] == -1) {
      jmap->first_jno_for_axno[axno] = jno;
    }
  }

  return 0;
}

int init_hal_params(int comp_id, haldata_t *haldata) {
  const char *coord_letter = "xyz";
  int res = 0;

  if (haldata == NULL) {
    return -EINVAL;
  }

  // Calibration matrices A, B, and vector C
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      if ((res = hal_param_float_newf(HAL_RW, &haldata->calib_m_A[i][j],
                                      comp_id, "calibxzkins.calib-a.%c%c",
                                      coord_letter[i], coord_letter[j])) < 0) {
        return res;
      }

      if ((res = hal_param_float_newf(HAL_RW, &haldata->calib_m_B[i][j],
                                      comp_id, "calibxzkins.calib-b.%c%c",
                                      coord_letter[i], coord_letter[j])) < 0) {
        return res;
      }
    }

    if ((res = hal_param_float_newf(HAL_RW, &haldata->calib_v_C[i], comp_id,
                                    "calibxzkins.calib-c.%c",
                                    coord_letter[i])) < 0) {
      return res;
    }
  }

  // Joints limits
  for (int i = 0; i < 3; ++i) {
    if ((res = hal_param_float_newf(HAL_RW, &(haldata->joints_min[i]), comp_id,
                                    "calibxzkins.min-limit.%c",
                                    coord_letter[i])) < 0) {
      return res;
    }

    if ((res = hal_param_float_newf(HAL_RW, &(haldata->joints_max[i]), comp_id,
                                    "calibxzkins.max-limit.%c",
                                    coord_letter[i])) < 0) {
      return res;
    }
  }

  // Initialize matrix A to identity, matrix B and vector C to zero
  memset((real_t *)haldata->calib_m_A, 0, sizeof(real_t) * 9);
  memset((real_t *)haldata->calib_m_B, 0, sizeof(real_t) * 9);
  memset((real_t *)haldata->calib_v_C, 0, sizeof(real_t) * 3);

  haldata->calib_m_A[0][0] = 1.0;
  haldata->calib_m_A[1][1] = 1.0;
  haldata->calib_m_A[2][2] = 1.0;

  // Initialize joints min/max to -inf/+inf
  for (int i = 0; i < 3; ++i) {
    haldata->joints_min[i] = -INFINITY;
    haldata->joints_max[i] = INFINITY;
  }

  return 0;
}

int init_hal_pins(int comp_id, haldata_t *haldata) {
  int res;

  if (haldata == NULL) {
    return -EINVAL;
  }

  if ((res = hal_pin_u32_newf(HAL_IO, &haldata->max_iter, comp_id,
                              "calibxzkins.max-iter")) < 0) {
    return res;
  }

  if ((res = hal_pin_float_newf(HAL_IO, &haldata->tol, comp_id,
                                "calibxzkins.tol")) < 0) {
    return res;
  }

  *haldata->max_iter = 10;
  *haldata->tol = 1e-3;

  return 0;
}

static int init_hal_data(int comp_id, haldata_t **haldata) {
  int res;

  *haldata = hal_malloc(sizeof(haldata_t));

  if (!*haldata) {
    return -ENOMEM;
  }

  if ((res = init_hal_params(comp_id, *haldata)) < 0) {
    rtapi_print_msg(RTAPI_MSG_ERR,
                    "calibxyzkins: error initializing hal parameters\n");
    return res;
  }

  if ((res = init_hal_pins(comp_id, *haldata)) < 0) {
    rtapi_print_msg(RTAPI_MSG_ERR,
                    "calibxyzkins: error initializing hal pins\n");
    return res;
  }

  return 0;
}

int calib_xyz_kins_setup(int comp_id, const char *coordinates,
                         const int max_joints, const int allow_duplicates,
                         haldata_t **haldata,
                         joints_mapping_t *joints_mapping) {
  const char *errtag = "calibxyzkins";
  int res;

  // Initialize joints mapping data
  if ((res = init_joints_mapping(coordinates, max_joints, allow_duplicates,
                                 joints_mapping)) < 0) {
    return res;
  }

  /*
   * Check that X, Y, and Z axis are set. If any of X, Y, and Z are not set
   * print an error and return.
   */
  if (joints_mapping->first_jno_for_axno[0] == -1 ||
      joints_mapping->first_jno_for_axno[1] == -1 ||
      joints_mapping->first_jno_for_axno[2] == -1) {
    rtapi_print_msg(RTAPI_MSG_ERR,
                    "%s: kinematics needs X, Y, and Z coordinates\n", errtag);
    return -EINVAL;
  }

  /*
   * print message for unconventional coordinates ordering;
   *   a) duplicate coordinate letters
   *   b) letters not ordered by "XYZABCUVW" sequence
   */
  bool show = false;
  for (int jno = 0; jno < EMCMOT_MAX_AXIS; jno++) {
    int axno = joints_mapping->axno_for_jno[jno];
    if (axno == -1) {
      break;
    }
    if (axno != jno) {
      show = true;
      break;
    }
  }

  if (show) {
    rtapi_print("%s: coordinates: %s\n", errtag, coordinates);
    char *coord_letters = "XYZABCUVW";
    for (int jno = 0; jno < EMCMOT_MAX_AXIS; jno++) {
      int axno = joints_mapping->axno_for_jno[jno];
      if (axno == -1) {
        break;
      }
      rtapi_print("   Joint %d ==> Axis %c\n", jno, coord_letters[axno]);
    }
    rtapi_print("\n");
  }

  // Initialize hal data
  if ((res = init_hal_data(comp_id, haldata)) < 0) {
    return res;
  }

  return 0;
}

/*
 * Read calibration params from the HAL data
 * This copies the volatile doubles data to doubles.
 */
static void read_hal_calibration_params(const haldata_t *haldata,
                                        double A[3][3], double B[3][3],
                                        double C[3]) {
  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      A[i][j] = haldata->calib_m_A[i][j];
      B[i][j] = haldata->calib_m_B[i][j];
    }
    C[i] = haldata->calib_v_C[i];
  }
}

/*
 * Read the joints min/max params from the HAL data
 * This copies the volatile doubles data to doubles.
 */
static void read_hal_joints_limits_params(const haldata_t *haldata,
                                          double joints_min[3],
                                          double joints_max[3]) {
  for (int i = 0; i < 3; ++i) {
    joints_min[i] = haldata->joints_min[i];
    joints_max[i] = haldata->joints_max[i];
  }
}

/*
 * Update positions from joints
 */
int calib_xyz_kins_forward(const joints_mapping_t *joints_mapping,
                           const haldata_t *haldata, const double *joints,
                           EmcPose *pos) {
  double A[3][3];
  double B[3][3];
  double C[3];

  double xyz_joints[3] = {
      joints[joints_mapping->first_jno_for_axno[0]],
      joints[joints_mapping->first_jno_for_axno[1]],
      joints[joints_mapping->first_jno_for_axno[2]],
  };

  double xyz_pos[3];

  read_hal_calibration_params(haldata, A, B, C);

  // Get calibrated XYZ position values from XYZ joint values
  calib_xyz_forward(A, B, C, xyz_joints, xyz_pos);

  for (int jno = 0; jno < EMCMOT_MAX_JOINTS; ++jno) {
    int axno = joints_mapping->axno_for_jno[jno];
    if (axno == -1) {
      break;
    }
    // clang-format off
    switch (axno) {
      case 0: pos->tran.x = xyz_pos[0]; break;
      case 1: pos->tran.y = xyz_pos[1]; break;
      case 2: pos->tran.z = xyz_pos[2]; break;
      case 3: pos->a = joints[joints_mapping->first_jno_for_axno[axno]]; break;
      case 4: pos->b = joints[joints_mapping->first_jno_for_axno[axno]]; break;
      case 5: pos->c = joints[joints_mapping->first_jno_for_axno[axno]]; break;
      case 6: pos->u = joints[joints_mapping->first_jno_for_axno[axno]]; break;
      case 7: pos->v = joints[joints_mapping->first_jno_for_axno[axno]]; break;
      case 8: pos->w = joints[joints_mapping->first_jno_for_axno[axno]]; break;
    }
    // clang-format on
  }

  return 0;
}

/*
 * Update joints (including joints for duplicate letters) from positions
 */
int calib_xyz_kins_inverse(const joints_mapping_t *joints_mapping,
                           const haldata_t *haldata, const EmcPose *pos,
                           double *joints) {
  double A[3][3];
  double B[3][3];
  double C[3];
  double joints_min[3];
  double joints_max[3];

  double xyz_pos[3] = {pos->tran.x, pos->tran.y, pos->tran.z};
  double xyz_joints[3];

  read_hal_calibration_params(haldata, A, B, C);
  read_hal_joints_limits_params(haldata, joints_min, joints_max);

  // Get calibrated XYZ joint values from XYZ position values
  // The returned joint values are within the specified bounds
  calib_xyz_inverse(A, B, C, joints_min, joints_max, *haldata->max_iter,
                    *haldata->tol, xyz_pos, xyz_joints, NULL);

  for (int jno = 0; jno < EMCMOT_MAX_JOINTS; ++jno) {
    int axno = joints_mapping->axno_for_jno[jno];
    if (axno == -1) {
      break;
    }
    // clang-format off
    switch (axno) {
      case 0: joints[jno] = xyz_joints[0]; break;
      case 1: joints[jno] = xyz_joints[1]; break;
      case 2: joints[jno] = xyz_joints[2]; break;
      case 3: joints[jno] = pos->a; break;
      case 4: joints[jno] = pos->b; break;
      case 5: joints[jno] = pos->c; break;
      case 6: joints[jno] = pos->u; break;
      case 7: joints[jno] = pos->v; break;
      case 8: joints[jno] = pos->w; break;
    }
    // clang-format on
  }

  return 0;
}
