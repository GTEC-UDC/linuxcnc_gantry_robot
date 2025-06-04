#include <math.h>

#include "../calibxyzlib.h"
#include "unity.h"

void setUp(void) {}

void tearDown(void) {}

void run_test_calib_xyz(double A[3][3], double B[3][3], double C[3],
                        double min_bounds[3], double max_bounds[3],
                        double joints[3]) {
  double position[3];
  double joints_result[3];
  int maxiter = 20;
  double tol = 1e-5;
  double F_norm;

  // Get position from joints
  calib_xyz_forward(A, B, C, joints, position);

  // Get joints from position
  calib_xyz_inverse(A, B, C, min_bounds, max_bounds, maxiter, tol, position,
                    joints_result, &F_norm);

  // Check optimization function norm
  TEST_ASSERT_DOUBLE_WITHIN(5 * tol, 0, F_norm);

  // Check obtained joints
  TEST_ASSERT_DOUBLE_ARRAY_WITHIN(5 * tol, joints, joints_result, 3);
}

void run_many_test_calib_xyz(double A[3][3], double B[3][3], double C[3],
                             double min_bounds[3], double max_bounds[3],
                             double step_x, double step_y, double step_z) {
  double joints[3];

  for (double x = min_bounds[0]; x <= max_bounds[0]; x += step_x) {
    joints[0] = x;
    for (double y = min_bounds[1]; y <= max_bounds[1]; y += step_y) {
      joints[1] = y;
      for (double z = min_bounds[2]; z <= max_bounds[2]; z += step_z) {
        joints[2] = z;
        run_test_calib_xyz(A, B, C, min_bounds, max_bounds, joints);
      }
    }
  }
}

void test_calib_xyz_identity(void) {
  double A[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double B[3][3] = {0};
  double C[3] = {0};
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};
  double step_x = 10, step_y = 10, step_z = 10;
  double position[3];

  // Check using only A set to the identity matrix
  TEST_ASSERT(calib_xyz_check_inv(A, B, min_bounds, max_bounds) == 0);
  run_many_test_calib_xyz(A, B, C, min_bounds, max_bounds, step_x, step_y,
                          step_z);

  // Check setting C to a non-zero value
  C[0] = 0.5;
  C[1] = 1;
  C[2] = 1.5;
  TEST_ASSERT(calib_xyz_check_inv(A, B, min_bounds, max_bounds) == 0);
  run_many_test_calib_xyz(A, B, C, min_bounds, max_bounds, step_x, step_y,
                          step_z);
}

void test_calib_xyz_general(void) {
  double A[3][3] = {{1, 0.025, 0}, {0.025, 1, 0}, {0, 0.1, 1}};
  double B[3][3] = {
      {0.002, 0.0005, 0}, {0.00025, 0.002, 0}, {0.001, 0.002, 0.0005}};
  double C[3] = {0.5, 1, 1.5};
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};
  double step_x = 10, step_y = 10, step_z = 10;
  double position[3];

  TEST_ASSERT(calib_xyz_check_inv(A, B, min_bounds, max_bounds) == 0);

  run_many_test_calib_xyz(A, B, C, min_bounds, max_bounds, step_x, step_y,
                          step_z);
}

void test_calib_xyz_check_fail(void) {
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};

  // Non invertible matrix A
  double A1[3][3] = {{1, 0.025, 0}, {0.025, 1, 0}, {0, 0.1, 0}};
  double B1[3][3] = {0};

  TEST_ASSERT(calib_xyz_check_inv(A1, B1, min_bounds, max_bounds) == -1);

  // Non invertible Jacobian J = A + 2*B*diag(x) for some x within the bounds
  // Note that for A = I, and B = I * a, being 'a' a real number greater than 0,
  // and having bounds = (b_l, b_u) for all coordinates, the Jacobian
  // J = I + 2*a*diag(x) is invertible for all x when 2*a*b_l > -1 and
  // 2*a*b_u < 1, or equivalently  -1/(2*b_l) < a < 1/(2*b_u)
  double A2[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double B2[3][3] = {{0.005, 0, 0}, {0, 0.005, 0}, {0, 0, 0.005}};

  TEST_ASSERT(calib_xyz_check_inv(A2, B2, min_bounds, max_bounds) == -2);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_calib_xyz_identity);
  RUN_TEST(test_calib_xyz_general);
  RUN_TEST(test_calib_xyz_check_fail);
  return UNITY_END();
}