(sec:calibxyzkins_module)=

# calibxyzkins - Calibrated XYZ Kinematics Module for LinuxCNC

The `calibxyzkins` module extends the standard LinuxCNC trivial kinematics module `trivkins` by applying a mathematical correction to compensate for systematic positioning errors in gantry robots and similar cartesian machines. This is particularly useful for correcting:

- Mechanical inaccuracies in manufacturing or assembly
- Structural deformations under load
- Non-perpendicular axes alignment
- Position-dependent errors

## Coordinate Transformation

The module implements a coordinate transformation that corrects the relationship between joint positions and actual machine coordinates using both linear and quadratic terms:

$[x', y', z']^T = \mathbf{A} [x, y, z]^T + \mathbf{B} [x^2, y^2, z^2]^T + \mathbf{c}$

Where:

- $(\cdot)^T$: Transpose operator
- $\mathbf{A}$: 3×3 linear transformation matrix (scaling, rotation, shear, etc.)
- $\mathbf{B}$: 3×3 quadratic transformation matrix (corrects non-linear distortions)
- $\mathbf{c}$: 3×1 offset vector (constant position offset)
- $x, y, z$: joint positions
- $x', y', z'$: axes coordinates

The default values of the parameters are:

- $\mathbf{A}$: 3x3 identity matrix
- $\mathbf{B}$: all zeros
- $\mathbf{c}$: all zeros

## Installation

Prerequisites:

- LinuxCNC development environment
- Standard build tools (make, gcc)

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

The module can be loaded as any other HAL component. Depending on the machine configuration, the `coordinates` and `kinstype` parameters can be used to specify the axis-to-joint mapping.

Examples:

- Basic usage (equivalent to `trivkins`):

  ```hal
  loadrt calibxyzkins
  ```

- Specify coordinate mapping:

  ```hal
  loadrt calibxyzkins coordinates=xyz
  ```

- Gantry configuration with duplicated Y axis:

  ```hal
  loadrt calibxyzkins coordinates=xyyz kinstype=B
  ```

## Module Parameters

- `coordinates`

  Specifies the axis-to-joint mapping, as in `trivkins`:
  
  - **coordinates=xyz**: Standard 3-axis mapping (X→joint0, Y→joint1, Z→joint2)
  - **coordinates=xyyz**: Gantry with dual Y motors (X→joint0, Y→joint1&joint2, Z→joint3)
  - **coordinates=xyzabc**: 6-axis machine. Note that calibration is only applied to the X, Y, and Z axes.

- `kinstype`

  Specifies the kinematics type, as in `trivkins`:
  
  - **kinstype=1**: KINEMATICS_IDENTITY (default)
  - **kinstype=B**: KINEMATICS_BOTH
  - **kinstype=F**: KINEMATICS_FORWARD_ONLY
  - **kinstype=I**: KINEMATICS_INVERSE_ONLY

## HAL Parameters

**Calibration Matrix A (Linear Terms)**:

- `calibxyzkins.calib-a.xx` (float, RW, default: 1.0)
- `calibxyzkins.calib-a.xy` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.xz` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.yx` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.yy` (float, RW, default: 1.0)
- `calibxyzkins.calib-a.yz` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.zx` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.zy` (float, RW, default: 0.0)
- `calibxyzkins.calib-a.zz` (float, RW, default: 1.0)

**Calibration Matrix B (Quadratic Terms)**:

- `calibxyzkins.calib-b.xx` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.xy` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.xz` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.yx` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.yy` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.yz` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.zx` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.zy` (float, RW, default: 0.0)
- `calibxyzkins.calib-b.zz` (float, RW, default: 0.0)

**Calibration Vector c (Offset Terms)**:

- `calibxyzkins.calib-c.x` (float, RW, default: 0.0)
- `calibxyzkins.calib-c.y` (float, RW, default: 0.0)
- `calibxyzkins.calib-c.z` (float, RW, default: 0.0)

**Joint Limits**:

- `calibxyzkins.min-limit.x` (float, RW, default: -∞)
- `calibxyzkins.min-limit.y` (float, RW, default: -∞)
- `calibxyzkins.min-limit.z` (float, RW, default: -∞)
- `calibxyzkins.max-limit.x` (float, RW, default: +∞)
- `calibxyzkins.max-limit.y` (float, RW, default: +∞)
- `calibxyzkins.max-limit.z` (float, RW, default: +∞)

## HAL Pins

**Inverse Kinematics Solver Settings**:

- `calibxyzkins.max-iter` (u32, IO, default: 10)
  - Maximum number of Newton-Raphson iterations for the inverse kinematics.
- `calibxyzkins.tol` (float, IO, default: 1e-3)
  - Convergence tolerance for the inverse kinematics solver.

## Inverse Kinematics

The module uses the Newton-Raphson method to solve the inverse kinematics problem iteratively:

1. Initialize the $3 \times 1$ vector of joint positions $\mathbf{x}$ to the target position $\mathbf{x'}$ (bounded by joint limits if specified)
2. Perform Newton-Raphson iterations until convergence or max iterations reached:
   1. Compute residual: $\mathbf{f} = \mathbf{A} \, \mathbf{x} + \mathbf{B} \, \mathbf{x}^2 + \mathbf{c} - \mathbf{x'}$
   2. Return if convergence reached ($\|\mathbf{f}\|_2 < \text{tolerance}$).
   3. Compute Jacobian: $\mathbf{J} = \mathbf{A} + 2 \, \mathbf{B} \, \text{diag}(\mathbf{x})$
   4. Update joints: $\mathbf{x} := \mathbf{x} - \mathbf{J}^{-1} \mathbf{f}$

## Debugging

Verbose output of the inverse kinematics solver can be enabled by compiling the code with the `CALIB_XYZ_INVERSE_PRINT_ITER` macro defined.