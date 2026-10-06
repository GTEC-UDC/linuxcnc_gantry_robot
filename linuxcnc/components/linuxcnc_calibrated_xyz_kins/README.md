# calibxyzkins - Calibrated XYZ Kinematics for LinuxCNC

A LinuxCNC kinematics module that provides coordinate transformations for cartesian machines to correct minor structural deviations and positioning errors.

## Overview

The `calibxyzkins` module extends the standard trivial kinematics by applying a mathematical correction to compensate for systematic positioning errors in gantry robots and similar cartesian machines. This is particularly useful for correcting:

- Mechanical inaccuracies in manufacturing or assembly
- Structural deformations under load
- Non-perpendicular axes alignment
- Position-dependent errors

## Coordinate Transformation

The module implements a coordinate transformation that corrects the relationship between joint positions and actual machine coordinates using a polynomial of degree $n$ without cross terms:

$$
\begin{bmatrix}
x' \\ y' \\ z'
\end{bmatrix} =
\mathbf{c} + \sum_{k=1}^{n} \mathbf{A}_k
\begin{bmatrix}
x^k \\ y^k \\ z^k
\end{bmatrix}
$$

Where:

- $\mathbf{c}$: 3×1 offset vector (constant position offset)
- $\mathbf{A}_1$: 3×3 linear transformation matrix (scaling, rotation, shear, etc.)
- $\mathbf{A}_2, \dots, \mathbf{A}_n$: 3×3 matrices of the higher-order terms (correct non-linear distortions)
- $x, y, z$: joint positions
- $x', y', z'$: axes coordinates

The degree $n$ is set when the module is loaded, with the `degree` module parameter, and is 1 by default. A coordinate that needs a lower degree than $n$ is handled by leaving at zero its column in the matrices of the higher powers.

The default values of the parameters are:

- $\mathbf{c}$: all zeros
- $\mathbf{A}_1$: 3x3 identity matrix
- $\mathbf{A}_2, \dots, \mathbf{A}_n$: all zeros

## Installation

### Prerequisites

- LinuxCNC development environment
- Standard build tools (make, gcc)

### Building

To build the module, run:

```bash
cd linuxcnc/components/linuxcnc_calibrated_xyz_kins
make
```

To install the module system-wide, run:

```bash
sudo make install
```

### Loading the Module

The module can be loaded as any other HAL component. Depending on the machine configuration, the `coordinates` parameter can be used to specify the axis-to-joint mapping, and the `degree` parameter to set the degree of the coordinate transformation.

Examples:

- Basic usage (equivalent to `trivkins`):

  ```hal
  loadrt calibxyzkins
  ```

- Specify coordinate mapping:

  ```hal
  loadrt calibxyzkins coordinates=xyz
  ```

- Gantry configuration with duplicated Y axis and a transformation of degree three:

  ```hal
  loadrt calibxyzkins coordinates=xyyz degree=3
  ```

## Module Parameters

### `coordinates`

Specifies the axis-to-joint mapping, as in `trivkins`:

- **coordinates=xyz**: Standard 3-axis mapping (X→joint0, Y→joint1, Z→joint2)
- **coordinates=xyyz**: Gantry with dual Y motors (X→joint0, Y→joint1&joint2, Z→joint3)
- **coordinates=xyzabc**: 6-axis machine. Note that calibration is only applied to the X, Y, and Z axes.

### `degree`

Specifies the degree $n$ of the coordinate transformation, an integer from 1 to 5 (default: 1). It sets the number of calibration matrices, and thus the HAL parameters that the module creates:

- **degree=1**: Linear transformation, with $\mathbf{A}_1$ and $\mathbf{c}$ (default)
- **degree=2**: Adds the quadratic terms, with $\mathbf{A}_2$
- **degree=3**: Adds the cubic terms, with $\mathbf{A}_3$

The module fails to load if the degree is outside this range. The maximum degree is set at compile time with the `CALIB_XYZ_MAX_DEGREE` macro.

## HAL Parameters

### Calibration Matrices A1 to An (Terms of Degree 1 to n)

For each $k$ from 1 to the value of the `degree` module parameter, the module creates nine parameters for the entries of $\mathbf{A}_k$, with `<k>` replaced by the number $k$:

- `calibxyzkins.calib-a<k>.xx` (float, RW, default: 1.0 for $k = 1$, 0.0 otherwise)
- `calibxyzkins.calib-a<k>.xy` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.xz` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.yx` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.yy` (float, RW, default: 1.0 for $k = 1$, 0.0 otherwise)
- `calibxyzkins.calib-a<k>.yz` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.zx` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.zy` (float, RW, default: 0.0)
- `calibxyzkins.calib-a<k>.zz` (float, RW, default: 1.0 for $k = 1$, 0.0 otherwise)

The `x`, `y`, `z` letters of each parameter name indicate the row and column of the entry in $\mathbf{A}_k$:

$$
\mathbf{A}_k =
\begin{bmatrix}
\texttt{xx} & \texttt{xy} & \texttt{xz} \\
\texttt{yx} & \texttt{yy} & \texttt{yz} \\
\texttt{zx} & \texttt{zy} & \texttt{zz}
\end{bmatrix}
$$

### Calibration Vector c (Offset Terms)

- `calibxyzkins.calib-c.x` (float, RW, default: 0.0)
- `calibxyzkins.calib-c.y` (float, RW, default: 0.0)
- `calibxyzkins.calib-c.z` (float, RW, default: 0.0)

### Joint Limits

- `calibxyzkins.min-limit.x` (float, RW, default: -∞)
- `calibxyzkins.min-limit.y` (float, RW, default: -∞)
- `calibxyzkins.min-limit.z` (float, RW, default: -∞)
- `calibxyzkins.max-limit.x` (float, RW, default: +∞)
- `calibxyzkins.max-limit.y` (float, RW, default: +∞)
- `calibxyzkins.max-limit.z` (float, RW, default: +∞)

## HAL Pins

### Inverse Kinematics Solver Settings

- `calibxyzkins.max-iter` (u32, IO, default: 10)
  - Maximum number of Newton-Raphson iterations for the inverse kinematics.
- `calibxyzkins.tol` (float, IO, default: 1e-3)
  - Convergence tolerance for the inverse kinematics solver.

## Inverse Kinematics

The module uses the Newton-Raphson method to solve the inverse kinematics problem iteratively. With:

- $\mathbf{x} = [x, y, z]^T$ the joint positions
- $\mathbf{x}' = [x', y', z']^T$ the target position
- $\mathbf{x}^k = [x^k, y^k, z^k]^T$ the element-wise $k$-th power of the joint positions

The procedure is:

1. Initialize the joint positions to the target position: $\mathbf{x} = \mathbf{x}'$ (bounded by joint limits if specified)

2. Compute the residual:

   $$\mathbf{r} = \mathbf{c} + \sum_{k=1}^{n} \mathbf{A}_k \mathbf{x}^k - \mathbf{x}'$$

3. Stop if convergence is reached ($\lVert \mathbf{r} \rVert_2 < \text{tolerance}$).

4. Compute the Jacobian:

   $$\mathbf{J} = \sum_{k=1}^{n} k \mathbf{A}_k \text{diag}(\mathbf{x})^{k-1}$$

5. Update the joint positions (bounded by joint limits if specified):

   $$\mathbf{x} \leftarrow \mathbf{x} - \mathbf{J}^{-1} \mathbf{r}$$

6. Repeat from step 2 until max iterations reached.

## Debugging

Verbose output of the inverse kinematics solver can be enabled by compiling the code with the `CALIB_XYZ_INVERSE_PRINT_ITER` macro defined.