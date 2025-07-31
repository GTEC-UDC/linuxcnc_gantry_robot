(sec:error_analysis_calibration)=

# Error Analysis and Calibration

The gantry robot system includes a calibration solution that leverages an existing [OptiTrack](https://optitrack.com/) motion capture system to measure and compensate for systematic positioning errors caused by minor structural deviations in the robot. This calibration system enables the gantry robot to achieve sub-centimeter precision across its entire work envelope.

:::{important}
It is assumed that the gantry data is the commanded position of the gantry robot and the OptiTrack data is the actual position of the gantry robot. After the calibration is complete it can be evaluated with several scripts, which correct the OptiTrack data with the calibration parameters and compare the obtained positions with the reference gantry data.
:::

The error analysis and calibration system consists of several scripts to process and analyze the data collected from both the gantry robot and the OptiTrack motion capture system:

1. **Raw Data Visualization**: `plot_movement_gantry.py` and `plot_movement_optitrack.py` scripts to visualize the raw gantry and OptiTrack data before calibration.

2. **Calibration**: `run_calibration.py` is the script that processes the raw data, performing the following steps:
   - **Alignment**: Temporal and spatial alignment of OptiTrack and gantry robot coordinate systems using translation, rotation, and time shift transformations.
   - **Correction**: Non-orthogonal and non-linear transformation of the OptiTrack data to correct errors intrinsic to the gantry robot.

3. **Analysis**: Various scripts for plotting and analyzing the gantry and OptiTrack data, which can be executed after the calibration is complete:
   - `check_params.py`: Check the calibration parameters.
   - `print_calibxyzkins_config.py`: Print the HAL configuration for the `calibxyzkins` module.
   - `plot_movement.py`: Visualize the gantry and OptiTrack path.
   - `plot_errors.py`: Plot positioning errors over time.
   - `plot_errors_scatter.py`: Plot positioning errors scatter plots.
   - `plot_errors_probability.py`: Plot positioning errors probability distributions.

After the calibration is performed, the calibration parameters can be used to correct the gantry position data with the `calibxyzkins` module of LinuxCNC included in this project (see {ref}`sec:calibxyzkins_module`).

:::{toctree}
:maxdepth: 2
:caption: Table of Contents

01_installation.md
02_calibration.md
03_usage.md
:::
