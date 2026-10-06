#include "../calibxyzlib.h"
#include "unity.h"
#include <errno.h>

void setUp(void) {}

void tearDown(void) {}

void run_test_calib_xyz(int degree, double A[CALIB_XYZ_MAX_DEGREE][3][3],
                        double c[3], double min_bounds[3], double max_bounds[3],
                        double joints[3]) {
  double position[3];
  double joints_result[3];
  int maxiter = 20;
  double tol = 1e-5;
  double test_tol = 5 * tol;
  double r_norm;

  // Get position from joints
  calib_xyz_forward(degree, A, c, joints, position);

  // Get joints from position
  calib_xyz_inverse(degree, A, c, min_bounds, max_bounds, maxiter, tol,
                    position, joints_result, &r_norm);

  // Check optimization function norm
  TEST_ASSERT_DOUBLE_WITHIN(test_tol, 0, r_norm);

  // Check obtained joints
  TEST_ASSERT_DOUBLE_ARRAY_WITHIN(test_tol, joints, joints_result, 3);
}

void run_many_test_calib_xyz(int degree, double A[CALIB_XYZ_MAX_DEGREE][3][3],
                             double c[3], double min_bounds[3],
                             double max_bounds[3], double step_x, double step_y,
                             double step_z) {
  double joints[3];

  for (double x = min_bounds[0]; x <= max_bounds[0]; x += step_x) {
    joints[0] = x;
    for (double y = min_bounds[1]; y <= max_bounds[1]; y += step_y) {
      joints[1] = y;
      for (double z = min_bounds[2]; z <= max_bounds[2]; z += step_z) {
        joints[2] = z;
        run_test_calib_xyz(degree, A, c, min_bounds, max_bounds, joints);
      }
    }
  }
}

void test_calib_xyz_identity(void) {
  int degree = 1;
  double A[CALIB_XYZ_MAX_DEGREE][3][3] = {{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}};
  double c[3] = {0};
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};
  double step_x = 10, step_y = 10, step_z = 10;

  // Check using only A set to the identity matrix
  TEST_ASSERT(calib_xyz_check_inv(degree, A, min_bounds, max_bounds) == 0);
  run_many_test_calib_xyz(degree, A, c, min_bounds, max_bounds, step_x, step_y,
                          step_z);

  // Check setting c to a non-zero value
  c[0] = 0.5;
  c[1] = 1;
  c[2] = 1.5;

  TEST_ASSERT(calib_xyz_check_inv(degree, A, min_bounds, max_bounds) == 0);
  run_many_test_calib_xyz(degree, A, c, min_bounds, max_bounds, step_x, step_y,
                          step_z);
}

void test_calib_xyz_forward_values(void) {
  int degree = 3;
  double A[CALIB_XYZ_MAX_DEGREE][3][3] = {{{1, 2, 0}, {0, 1, 0}, {0, 0, 1}},
                                          {{0, 0, 1}, {1, 0, 0}, {0, 0, 0}},
                                          {{0, 0, 0}, {0, 0, 0}, {1, 1, 0}}};
  double c[3] = {10, 20, 30};
  double joints[3] = {2, 3, -1};
  double position[3];

  // x = 10 + (1*2 + 2*3) + 1*(-1)^2 = 19
  // y = 20 + 1*3 + 1*2^2 = 27
  // z = 30 + 1*(-1) + (1*2^3 + 1*3^3) = 64
  double expected[3] = {19, 27, 64};

  calib_xyz_forward(degree, A, c, joints, position);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, position, 3);

  // With degree == 2 the order 3 matrix must be ignored
  // z = 30 + 1*(-1) = 29
  expected[2] = 29;
  calib_xyz_forward(2, A, c, joints, position);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, position, 3);
}

void test_calib_xyz_general(void) {
  double A[CALIB_XYZ_MAX_DEGREE][3][3] = {
      {{1, 0.025, 0}, {0.025, 1, 0}, {0, 0.1, 1}},
      {{0.002, 0.0005, 0}, {0.00025, 0.002, 0}, {0.001, 0.002, 0.0005}},
      {{2e-6, 0, 1e-8}, {-1e-7, 1e-6, 0}, {1e-8, 0, 1.25e-6}},
      {{1e-8, 1e-9, 1e-9}, {-1e-9, 1e-8, 0}, {0, 1.25e-8, 0}},
      {{1.45e-10, 0, 1e-12}, {-1e-11, 0.85e-10, 0}, {0.25e-11, 0, 0.9e-10}}};

  double c[3] = {0.5, 1, 1.5};
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};
  double step_x = 10, step_y = 10, step_z = 10;

  for (int degree = 1; degree <= CALIB_XYZ_MAX_DEGREE; ++degree) {
    TEST_ASSERT(calib_xyz_check_inv(degree, A, min_bounds, max_bounds) == 0);
    run_many_test_calib_xyz(degree, A, c, min_bounds, max_bounds, step_x,
                            step_y, step_z);
  }

  // Higher order terms too large for the bounds
  A[4][0][0] = 1e-8;
  TEST_ASSERT(calib_xyz_check_inv(4, A, min_bounds, max_bounds) == 0);
  TEST_ASSERT(calib_xyz_check_inv(5, A, min_bounds, max_bounds) == -2);
}

void test_calib_xyz_check_fail(void) {
  double min_bounds[3] = {-100, -100, -100};
  double max_bounds[3] = {100, 100, 100};

  // Non invertible matrix A
  int degree = 1;
  double A1[CALIB_XYZ_MAX_DEGREE][3][3] = {
      {{1, 0.025, 0}, {0.025, 1, 0}, {0, 0.1, 0}}};

  TEST_ASSERT(calib_xyz_check_inv(degree, A1, min_bounds, max_bounds) == -1);

  // Non invertible Jacobian for some x within the bounds.
  // With A_1 = I and A_2 = a * I, a > 0, the Jacobian is
  //   J = A_1 + 2 * A_2 * diag(x) = I + 2 * a * diag(x)
  // which is singular when x_i = -1 / (2 * a) for any x_i.
  // For example, for a = 0.006, x_i = -83.3, and the check
  // must fail.
  degree = 2;
  double A2[CALIB_XYZ_MAX_DEGREE][3][3] = {
      {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}},
      {{0.006, 0, 0}, {0, 0.006, 0}, {0, 0, 0.006}}};

  TEST_ASSERT(calib_xyz_check_inv(degree, A2, min_bounds, max_bounds) == -2);
}

void test_calib_xyz_check_non_finite(void) {
  double min_bounds[3] = {-100, -100, -INFINITY};
  double max_bounds[3] = {100, 100, INFINITY};

  // Z is not bounded, but its column is zero in A_2: check must pass
  double A[CALIB_XYZ_MAX_DEGREE][3][3] = {
      {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}},
      {{0.001, 0.001, 0}, {0, 0.001, 0}, {0.001, 0, 0}}};

  TEST_ASSERT(calib_xyz_check_inv(2, A, min_bounds, max_bounds) == 0);

  // Z is not bounded and has a quadratic term: check must fail
  A[1][2][2] = 1e-6;
  TEST_ASSERT(calib_xyz_check_inv(2, A, min_bounds, max_bounds) == -2);

  // NaN in the matrices
  A[1][2][2] = NAN;
  TEST_ASSERT(calib_xyz_check_inv(2, A, min_bounds, max_bounds) == -2);
  A[0][0][0] = NAN;
  TEST_ASSERT(calib_xyz_check_inv(1, A, min_bounds, max_bounds) == -1);

  // NaN in the bounds
  A[0][0][0] = 1;
  A[1][2][2] = 0;
  min_bounds[0] = NAN;
  TEST_ASSERT(calib_xyz_check_inv(2, A, min_bounds, max_bounds) == -EINVAL);
  min_bounds[0] = -100;
  max_bounds[2] = NAN;
  TEST_ASSERT(calib_xyz_check_inv(2, A, min_bounds, max_bounds) == -EINVAL);
}

void test_calib_xyz_inverse_fail(void) {
  // Singular Jacobian: the inverse must return an error
  double A[CALIB_XYZ_MAX_DEGREE][3][3] = {
      {{1, 0.025, 0}, {0.025, 1, 0}, {0, 0.1, 0}}};
  double c[3] = {0};
  double position[3] = {1, 2, 3};
  double joints[3];

  TEST_ASSERT(calib_xyz_inverse(1, A, c, NULL, NULL, 20, 1e-5, position, joints,
                                NULL) == -1);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_calib_xyz_identity);
  RUN_TEST(test_calib_xyz_forward_values);
  RUN_TEST(test_calib_xyz_general);
  RUN_TEST(test_calib_xyz_check_fail);
  RUN_TEST(test_calib_xyz_check_non_finite);
  RUN_TEST(test_calib_xyz_inverse_fail);
  return UNITY_END();
}