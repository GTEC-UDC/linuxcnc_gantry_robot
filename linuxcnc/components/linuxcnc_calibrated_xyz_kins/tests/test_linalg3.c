#include "../linalg3.h"
#include "unity.h"
#include <stdio.h>

void setUp(void) {}

void tearDown(void) {}

void test_function_det_m_3x3_identity(void) {
  double matrix[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  TEST_ASSERT(det_m_3x3(matrix) == 1.0);
}

void test_function_det_m_3x3_non_invertible(void) {
  double matrix[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 0}};
  TEST_ASSERT(det_m_3x3(matrix) == 0);
}

void test_function_det_m_3x3_invertible(void) {
  double matrix[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};
  TEST_ASSERT_EQUAL_DOUBLE(1, det_m_3x3(matrix));
}

void test_function_inv_m_3x3_identity(void) {
  double matrix[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double inverse[3][3];

  TEST_ASSERT(inv_m_3x3(matrix, inverse) == 0);

  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      TEST_ASSERT(inverse[i][j] == (i == j));
    }
  }
}

void test_function_inv_m_3x3_non_invertible(void) {
  double matrix[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 0}};
  double inverse[3][3] = {0};

  TEST_ASSERT(inv_m_3x3(matrix, inverse) < 0);

  for (int i = 0; i < 3; ++i) {
    for (int j = 0; j < 3; ++j) {
      TEST_ASSERT(inverse[i][j] == 0.0);
    }
  }
}

void test_function_inv_m_3x3_invertible(void) {
  double matrix[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};
  double inverse_check[3][3] = {{4, -5, -2}, {5, -6, -2}, {-8, 9, 3}};
  double inverse[3][3];

  TEST_ASSERT(inv_m_3x3(matrix, inverse) == 0);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(inverse_check, inverse, 9);
}

void test_function_mult_mm_3x3_identity(void) {
  double matrix1[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double matrix2[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};
  double result[3][3] = {0};

  mult_mm_3x3(matrix1, matrix2, result);
  TEST_ASSERT_DOUBLE_ARRAY_WITHIN(0, matrix2, result, 9);
}

void test_function_mult_mm_3x3_general(void) {
  double matrix1[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};
  double matrix2[3][3] = {{1, 2, -4}, {2, -1, 2}, {3, 2, -1}};
  double expected1[3][3] = {{-12, -1, -4}, {-13, 2, -10}, {8, -8, 19}};
  double expected2[3][3] = {{14, -27, -10}, {-7, 6, 0}, {5, -21, -11}};
  double result[3][3];

  mult_mm_3x3(matrix1, matrix2, result);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected1, result, 9);

  mult_mm_3x3(matrix2, matrix1, result);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected2, result, 9);
}

void test_function_mult_mv_3x3_identity(void) {
  double matrix[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double vector[3] = {1, 2, 3};
  double result[3];

  mult_mv_3x3(matrix, vector, result);
  TEST_ASSERT_DOUBLE_ARRAY_WITHIN(0, vector, result, 3);
}

void test_function_mult_mv_3x3_general(void) {
  double matrix[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};
  double vector[3] = {1, 2, 3};
  double expected[3] = {-12, -13, 8};
  double result[3];

  mult_mv_3x3(matrix, vector, result);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, result, 3);
}

void test_function_sum_vv_3_identity(void) {
  double vector1[3] = {1, 2, 3};
  double vector2[3] = {0};
  double result[3];

  sum_vv_3(vector1, vector2, result);
  TEST_ASSERT_DOUBLE_ARRAY_WITHIN(0, vector1, result, 3);
}

void test_function_sum_vv_3_general(void) {
  double vector1[3] = {1, 2, 3};
  double vector2[3] = {4, 5, 6};
  double expected[3] = {5, 7, 9};
  double result[3];

  sum_vv_3(vector1, vector2, result);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, result, 3);

  sum_vv_3(vector2, vector1, result);
  TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, result, 3);
}

void test_function_norm_1_m_3x3(void) {
  double matrix1[3][3] = {0};
  double matrix2[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double matrix3[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};

  TEST_ASSERT(norm_1_m_3x3(matrix1) == 0.0);
  TEST_ASSERT(norm_1_m_3x3(matrix2) == 1.0);
  TEST_ASSERT_EQUAL_DOUBLE(11, norm_1_m_3x3(matrix3));
}

void test_function_norm_inf_m_3x3(void) {
  double matrix1[3][3] = {0};
  double matrix2[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
  double matrix3[3][3] = {{0, -3, -2}, {1, -4, -2}, {-3, 4, 1}};

  TEST_ASSERT(norm_inf_m_3x3(matrix1) == 0.0);
  TEST_ASSERT(norm_inf_m_3x3(matrix2) == 1.0);
  TEST_ASSERT_EQUAL_DOUBLE(8, norm_inf_m_3x3(matrix3));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_function_det_m_3x3_identity);
  RUN_TEST(test_function_det_m_3x3_non_invertible);
  RUN_TEST(test_function_det_m_3x3_invertible);
  RUN_TEST(test_function_inv_m_3x3_identity);
  RUN_TEST(test_function_inv_m_3x3_non_invertible);
  RUN_TEST(test_function_inv_m_3x3_invertible);
  RUN_TEST(test_function_mult_mm_3x3_identity);
  RUN_TEST(test_function_mult_mm_3x3_general);
  RUN_TEST(test_function_mult_mv_3x3_identity);
  RUN_TEST(test_function_mult_mv_3x3_general);
  RUN_TEST(test_function_sum_vv_3_identity);
  RUN_TEST(test_function_sum_vv_3_general);
  RUN_TEST(test_function_norm_1_m_3x3);
  RUN_TEST(test_function_norm_inf_m_3x3);
  return UNITY_END();
}