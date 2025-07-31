(sec:page_axis)=

# "Axis" Page

The "Axis" configuration page is shown below in {numref}`fig:conf_x1_axis`. The parameters use the units established on the initial configuration page (see {numref}`sec:conf_start`); thus, position parameters are in millimeters (mm), speed parameters in millimeters per second (mm/s), and acceleration parameters in millimeters per second squared (mm/s{sup}`2`). The various options available on this page and their settings for our gantry robot configuration are described in the following sections.

:::{figure} images/config-x1/03-axis.png
:name: fig:conf_x1_axis

"Axis" configuration page of the X1 motor controller.
:::

## Axis Configuration Summary

{numref}`tab:axis_config_summary` below summarizes the configuration parameters for the axes:

:::{tabularcolumns} l\R{0.24}\R{0.24}
:::

:::{csv-table} Axis configuration summary for the gantry robot.
:name: tab:axis_config_summary
:widths: auto
:header: Parameter,Value (X1/X2/Y),Value (Z)
:class: longtable align-col2-r align-col3-r

**Axis**,,
Minimal Stroke (mm),0,0
Maximal Stroke (mm),0,0
Feed Rate (mm/s),144,4
**Motion Limits**,,
Max. Velocity (mm/s),720,50
Jog Velocity (mm/s),100,20
Max. Acceleration (mm/s{sup}`2`),300,3200
S-Curve (%),0,0
Quick-Stop (mm/s{sup}`2`),500,200
Following Error (mm),10,1
Positioning Window (mm),0,0
Positioning Time (ms),0,0
**Limit Switch**,,
Position,None,None
**Reference**,,
Method, SCP (Set Current Position), SCP (Set Current Position)
Offset (mm),0,0
**Absolute Feedback**,,
AI 1 Target Value Min. (V),-10,N/A
AI 1 Target Value Max. (V),10,N/A
AI 1 Dead Band Zero Value (V),0,N/A
AI 1 Dead Band Input Signal (V),0,N/A
AI 1 Filter (ms),10,N/A
AI 2 Absolute Value Min (V),N/A,N/A
AI 2 Absolute Value Max (V),N/A,N/A
:::

## Axis

This section contains the following parameters:

- **Minimal Stroke** and **Maximal Stroke**: These parameters specify the movement window for "ABS" mode (Absolute Positioning). Since we will not be using this mode, these parameters are not relevant to our application and they are both set to 0.

- **Feed Rate**: For linear axes, this parameter indicates the axis displacement per motor rotation. In our gantry robot setup the motors have the following feed rates:

  - **Brushless motors (X1, X2, Y)**: 144 mm/rev
  - **Stepper motor (Z)**: 4 mm/rev

(sec:axis_motion_limits)=

## Motion Limits

This section includes the following parameters:

- **Max. Velocity (mm/s)**: This sets the maximum motor speed. It functions as a limit for the movement programming modes available on the "Drive Profile" page (see {numref}`sec:page_drive_profile`). For the stepper motor (Z), speed will be controlled by the step signal received by the controller. For the brushless motors (X1, X2, Y), the maximum speed will be set on the "Drive Profile" page, with a value not exceeding that set here. In our gantry robot setup, we have configured the following values:

  - **Brushless motors (X1, X2, Y)**: 720 mm/s
  - **Stepper motor (Z)**: 50 mm/s

- **Jog Velocity (mm/s)**: This parameter defines the motor speed for manual positioning, accessible on the "Drive Profile" page (see {numref}`sec:page_drive_profile`). It is primarily useful for testing purposes via the controller's web interface. For the final system, this parameter is irrelevant.

- **Max. Acceleration (mm/s{sup}`2`)**: This sets the maximum motor acceleration, used in manual positioning on the "Drive Profile" page (see {numref}`sec:page_drive_profile`). It also serves as a limit in the movement programming modes available on the "Drive Profile" page. Similar to speed, for the stepper motor (Z), acceleration will be controlled by the step signal received by the controller. For the brushless motors (X1, X2, Y), the maximum acceleration will also be set on the "Drive Profile" page, with a value not exceeding that set here.
  
  :::{important}
  We have experimentally found that for the step/direction drive mode, the maximum acceleration also controls the jerk, i.e, the maximum rate of change of the acceleration over time, thus for the stepper motor (Z) we have set the maximum acceleration to a relatively high value.
  :::
  
  In our gantry robot setup, we have configured the following values:

  - **Brushless motors (X1, X2, Y)**: 300 mm/s{sup}`2`
  - **Stepper motor (Z)**: 3200 mm/s{sup}`2`

- **S-Curve (%)**: This parameter allows control over the rate of change of acceleration, known as "jerk" {cite}`enwiki:1178778094`. It can be adjusted between 0% and 100% to control the smoothness of acceleration and deceleration transitions in motor movement. Lower values will result in abrupt changes in acceleration, leading to higher "jerk" levels and, consequently, less smooth movements that can induce unwanted vibrations and stress on the system. Conversely, higher values will reduce "jerk," resulting in smoother acceleration and deceleration transitions, thereby minimizing vibrations and wear on both the motor and machinery.

  If an external controller (such as LinuxCNC) is to have full control over motor movement, this parameter should be set to 0%. In this configuration, any acceleration and deceleration smoothing within the motor controller itself is deactivated, allowing the external controller to directly manage the movement.

  However, LinuxCNC's current motion controller does not have a "jerk" limitation and uses constant acceleration. It might be desirable to set this parameter to a value greater than 0% to limit "jerk" and prevent unwanted vibrations and stress on the system. However, this approach would increase tracking error within LinuxCNC. Therefore, if this option is to be set above 0%, a balance between movement smoothness and tracking precision must be found.

  In our gantry robot setup, we have set the parameter to 0%.

- **Quick-Stop (mm/s{sup}`2`)**: This specifies the deceleration rate when a movement stops in an emergency. A quick stop is executed if the controller's "Enable" signal (digital input X2.7) is revoked.

  :::{important}
  It is important to ensure that the specified deceleration is appropriate for the intended application. A deceleration that is too low could result in an excessive stop time for the robot's movement; conversely, a deceleration that is too high could damage the robot's mechanical structure.
  :::

  In our gantry robot setup, we have configured the following values:

  - **Brushless motors (X1, X2, Y)**: 500 mm/s{sup}`2`
  - **Stepper motor (Z)**: 200 mm/s{sup}`2`

- **Following Error (mm)**: This defines the permissible deviation of the actual position from the desired position. A warning is issued if 50% of the allowed tracking error is reached. If the allowed tracking error is exceeded, the movement stops, and an error is reported.

  In our gantry robot setup, we have configured the following values:
  
  - **Brushless motors (X1, X2, Y)**: 10 mm
  - **Stepper motor (Z)**: 1 mm

- **Positioning Window (mm)**: This parameter defines a position range around a target point, extending in both positive and negative directions. For example, if the goal is to reach 100 mm and a positioning window of 10 mm is set, the system will consider the position to be within the target range if it falls anywhere between 90 mm and 110 mm. If the motor's actual position is within this window, the movement is considered complete, even if the motor is mechanically blocked. This prevents the system from continuously attempting to reach an exact position in case of an obstruction. If the positioning window is set to 0, this function is deactivated, and the system will not consider a range around the target point.

  In our gantry robot setup, we have set this parameter to 0, thereby deactivating this function.

- **Positioning Time (ms)**: This defines the duration, in milliseconds, for which the actual position must be maintained within the range defined by the positioning window before a movement is considered complete.

  In our gantry robot setup, we have set this parameter to 0.

(sec:limit_switch)=

## Limit Switch

This section includes a "Position" parameter that allows for specifying the position and number of limit sensors used.

In our gantry robot setup, the limit sensors are not connected to the controllers, they are only connected to the MESA 7I96S board, so limits are entirely managed by LinuxCNC. Therefore, we set the "Position" parameter to "None."

## Reference

This section allows for selecting the preferred referencing ("homing") method and position displacement ("offset").

Similar to robot movement limits (see {numref}`sec:limit_switch`), the "homing" process will also be fully controlled by LinuxCNC. Therefore, we have set the following parameters:

- **Method**: SCP (Set Current Position)
- **Offset (mm)**: 0

(sec:axis_absolute_feedback)=

## Absolute Feedback

The igus® dryve D1 controller has two analog inputs, AI 1 (Analog Input 1, input X4.1) and AI 2 (Analog Input 2, input X4.2). These are used to configure and control the target position or speed and the current position of the system, respectively. In our system, we will use analog input AI 1 to control the speed of the brushless motors (X1, X2, Y). Analog input AI 2 will not be used. For the stepper motor (Z), these inputs are not applicable, making this section relevant only for the brushless motors. Below are the parameters related to the analog inputs available in this section.

- **Parameters related to AI 1 (input X4.1)**:

  The AI 1 input will be used to control the speed of the brushless motors (X1, X2, Y) (see {numref}`sec:page_drive_profile`). The analog input control voltage will be ± 10 V, which must be configured on the "Inputs/Outputs" page (see {numref}`sec:page_input_outputs`). This voltage range must be considered when setting the AI 1 related parameters detailed below.

  - **AI 1 Target Value Min. (V)**: The minimum voltage value at analog input AI 1. We set its value to -10 V.
  - **AI 1 Target Value Max. (V)**: The maximum voltage value at analog input AI 1. We set its value to 10 V.
  - **AI 1 Dead Band Zero Value (V)**: This allows for setting a dead band symmetrically around 0 V in the target signal corresponding to analog input AI 1. This parameter can be specified in increments of 0.001 V. We set its value to 0 V.
  - **AI 1 Dead Band Input Signal (V)**: This allows for setting a dead band symmetrically around 0 V in the input signal of Analog Input AI 1. This parameter can be specified in increments of 0.001 V. We set its value to 0 V.
  - **AI 1 Filter (ms)**: This is the interval for averaging the signal. It is used to filter sudden signal variations and prevent inconsistencies in movement. Lower values result in a system that responds quickly but is more susceptible to noise or interference. Higher values result in a more stable system but with a longer response time. We set its value to 10 ms.

  The dead band parameters, "AI 1 Dead Band Zero Value" and "AI 1 Dead Band Input Signal," can be used to minimize unwanted motor movements during the idle state caused by increased ripple in the input signal or other interferences. Considering the above parameters, if the analog input voltage $x$ is already filtered as specified in the "AI 1 Filter" parameter, the target position or speed will be calculated using the following transfer functions:

  - $f_{\text{ZV}}(\cdot)$, corresponding to the "AI 1 Dead Band Zero Value" parameter and shown in {numref}`fig:deadband_zv`.
  - $f_{\text{IS}}(\cdot)$, corresponding to the "AI 1 Dead Band Input Signal" parameter and shown in {numref}`fig:deadband_is`.

  Thus, for the analog input value $x$, the target position or speed will be:

  $$y = (f_{\text{ZV}} \circ f_{\text{IS}})(x) = f_{\text{ZV}}(f_{\text{IS}}(x))$$

  :::{note}
  The calculation of the target position or speed is not explicitly stated in the controller manual (considering manual version 3.0.1) and has been determined experimentally. The manual only textually describes the "AI 1 Dead Band Zero Value" and "AI 1 Dead Band Input Signal" parameters, similar to the descriptions provided above.
  :::

:::{figure} images/f_zv/fig.*
:name: fig:deadband_zv

Transfer function $f_{\text{ZV}}(\cdot)$.
:::

:::{figure} images/f_is/fig.*
:name: fig:deadband_is

Transfer function $f_{\text{IS}}(\cdot)$.
:::

- **Parameters related to AI 2 (input X4.2)**:

  Analog input AI 2 is used to provide position information to the controller via an analog signal. In our case, we will not be using this input, so the parameters related to it are irrelevant.

  - **AI 2 Absolute Value Min (V)**: The minimum voltage value at analog input AI 2.
  - **AI 2 Absolute Value Max (V)**: The maximum voltage value at analog input AI 2.
