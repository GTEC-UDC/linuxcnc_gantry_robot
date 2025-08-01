# Data and Calibration

(sec:data_format)=

## Data Format

The calibration system requires data from both the gantry robot and the OptiTrack motion capture system in specific CSV formats.

### Gantry Data (CSV)

The gantry data is a CSV file with the following columns:

- `time` - Unix time (seconds since 1970-01-01 00:00:00 UTC) as a floating-point number.
- `x`, `y`, `z` - Position coordinates in mm as floating-point numbers.

### OptiTrack Data (CSV)

The OptiTrack data is the CSV exported from the OptiTrack Motive software. The format follows this structure:

- **Line 1**: Header with metadata (format version, take name, capture frame rate, export frame rate, start time, total frames, rotation type, length units, coordinate space, etc.)
- **Line 2**: Blank line
- **Line 3**: Object types for each column (e.g., "Rigid Body", "Rigid Body Marker", "Marker")
- **Line 4**: Object names for each column (e.g., "Grua", "Grua:Marker1", "Active 1", "Unlabeled 1007")
- **Line 5**: Unique object IDs (hexadecimal identifiers for each marker/object)
- **Line 6**: Data types for each column ("Rotation" or "Position")
- **Line 7**: Column headers ("Frame", "Time (Seconds)", "X", "Y", "Z", "W" for quaternion rotation, then "X", "Y", "Z" for position coordinates)
- **Line 8 onwards**: Data rows containing:
  - Frame number (integer)
  - Time in seconds (floating-point)
  - Rotation and/or position coordinates.

:::{note}
Missing or untracked data points appear as empty cells in the CSV.
:::

## Calibration Process

The calibration process performs two steps: alignment and correction.

### Alignment

First, the OptiTrack data must be aligned with the gantry data to account for differences in coordinate systems and timing. This alignment process involves finding the following parameters:

- **Translation**: Shifts in X, Y, and Z axes
- **Rotation**: Rotations around X, Y, and Z axes. By default the rotation center is `(2500, 2500, -750)`, but it may be changed.
- **Time Shift**: Temporal alignment to account for timing differences.

The alignment parameters are found using numerical optimization, with the Powell method by default, to minimize the mean squared error between gantry and the aligned OptiTrack positions. The optimization is performed using the `scipy.optimize.minimize` function.

### Correction

Analysis of scatter plots of the positioning errors (see {numref}`sec:plot_errors_scatter`) reveals clear patterns in positioning errors:

- **Y-axis position affects errors in all axes**
- **X-axis position affects errors in the Y-axis**
- **Z-axis position affects errors in X and Y axes**

These systematic deviations can be corrected by applying a coordinate transformation when controlling the gantry robot. For this we consider a general coordinate transformation with both first-order and second-order components:

$$
\begin{bmatrix}
x' \\ y' \\ z'
\end{bmatrix} =
\underbrace{
\begin{bmatrix}
a_{11} & a_{12} & a_{13} \\ a_{21} & a_{22} & a_{23} \\ a_{31} & a_{32} & a_{33}
\end{bmatrix}
}_{\normalsize A}
\begin{bmatrix}
x \\ y \\ z
\end{bmatrix} +
\underbrace{
\begin{bmatrix}
b_{11} & b_{12} & 0 \\ b_{21} & b_{22} & 0 \\ b_{31} & b_{32} & 0
\end{bmatrix}
}_{\normalsize B}
\begin{bmatrix}
x^2 \\ y^2 \\ z^2
\end{bmatrix} +
\underbrace{
\begin{bmatrix}
c_1 \\ c_2 \\ c_3
\end{bmatrix}
}_{\normalsize C}
$$

where $x, y, z$ are the aligned OptiTrack position coordinates (the actual position of the gantry robot), $x', y', z'$ are the corrected position coordinates (the target position for the gantry control), and $A, B, C$ are the transformation matrices and vector that need to be optimized.

:::{note}
The third column of the second-order matrix $B$ is set to zero because the Z-axis measurement interval is small, making the $z^2$ term unreliable if $z$ is extrapolated.
:::

This transformation consists of:

1. Matrix $A$: Linear transformation that handles scaling, rotation, and shear.
2. Matrix $B$: Quadratic transformation that corrects non-linear distortions.
3. Vector $C$: Constant offset.

The correction parameters are found using numerical optimization, with the Powell method by default, to minimize the mean squared error between gantry and the corrected OptiTrack positions. The optimization is performed using the `scipy.optimize.minimize` function.

## Parameters Validation

The `calibxyzkins` module of LinuxCNC included in this project uses the Newton-Raphson algorithm to solve the inverse kinematics problem: given desired axes positions $x', y', z'$, it finds the corresponding joint positions $x, y, z$ that satisfy the transformation equation:

$$\mathbf{f}(x, y, z) = A \begin{bmatrix} x \\ y \\ z \end{bmatrix} + B \begin{bmatrix} x^2 \\ y^2 \\ z^2 \end{bmatrix} + C = \begin{bmatrix} x' \\ y' \\ z' \end{bmatrix}$$

To ensure the calibration parameters are valid we include the `check_params.py` script, which performs the following validation tests:

### Jacobian Invertibility Test

The Newton-Raphson method requires computing the Jacobian matrix of the transformation function:

$$J = \frac{\partial \mathbf{f}}{\partial [x, y, z]} = A + 2 \cdot \text{diag}(x, y, z) \cdot B$$

The Jacobian matrix must be invertible throughout the robot's workspace. This is tested using an approach based on the Neumann series.

The Neumann series states that $(I - T)$ is invertible if $\|T\| < 1$, where $I$ is the identity matrix and $\|\cdot\|$ denotes a matrix norm.

For a matrix of the form $X + Y = X(I + X^{-1}Y)$, the matrix has an inverse if $\|X^{-1}Y\| < 1$.

Applying this to our Jacobian:

- $X = A$
- $Y = 2 \cdot \text{diag}(x, y, z) \cdot B$

Therefore, the Jacobian $J$ is invertible if $A$ is invertible and $\|2 \cdot A^{-1} \cdot \text{diag}(x, y, z) \cdot B\| < 1$ for the maximum absolute values of $x, y, z$ in the joint space bounds.

This condition is checked in the `check_params.py` script using both the 1-norm and infinity-norm.

### Bounds Test

The coordinate transformation must respect the physical limits of the robot, i.e., the desired axes positions $(x', y', z')$ must be within the robot's axes limits, and the corresponding joint positions $(x, y, z)$ computed by the inverse kinematics must be within the robot's joint limits.

This condition is checked in the `check_params.py` script by finding the minimum and maximum values that each joint can reach when the axes positions are constrained to their limits. These values must fall within the specified joint limits of the robot for the parameters to be valid.
