(sec:page_input_outputs)=
# "Inputs/Outputs" Page 

The "Inputs/Outputs" configuration page, displayed in {numref}`fig:conf_stepper_5`, allows for configuring the controller's inputs and outputs.

:::{figure} images/config-stepper/05-inputs_outputs.png
:name: fig:conf_stepper_5

"Inputs/Outputs" configuration page of the stepper motor controller.
:::

The digital logic level used by the controller is set by supplying input X2.11 with a voltage between 5 V and 24 V. The controller's digital logic operates as follows:

- Digital outputs are set to 0 V for a low level (L) and to the voltage of X2.11 for a high level (H).
- Digital inputs will be evaluated as a low level (L) for voltages between 0% and 10% of the X2.11 voltage, and as a high level (H) for values exceeding 60% of the X2.11 voltage.

These levels are illustrated in {numref}`fig:controller_logic_levels`.

:::{figure} images/logic_levels/fig.*
:name: fig:controller_logic_levels

Controller digital logic levels.
:::

To interact with the controller's digital inputs and outputs, we use the MESA 7I96S and 7I77 boards:

- The MESA 7I96S board transmits step and direction signals to the stepper motor controller; these signals operate on 5 V logic.
- The MESA 7I77 board sends "start" and "enable" signals, and reads the "ready," "alert," and "error" outputs from the controllers (refer to the wiring diagram in the {{project_url_link}}. The logic voltage for the MESA 7I77 board can be adjusted by supplying input TB2.1 ("field power") with the desired voltage, ranging from 5 V to 28 V.

Because the MESA 7I96S board can only use 5 V logic for step and direction signals, we have set the logic voltage for both the igus® dryve D1 controllers (X2.11 input) and the MESA 7I77 board (TB2.1 input) to 5 V.

The sections available on this page are:

- **Digital Inputs**: This section shows the digital inputs and allows you to select between normally open (H) or normally closed (L) for each. Normally open (H) inputs will activate upon receiving a high signal. Conversely, normally closed (L) inputs will activate upon receiving a low signal. We will keep all inputs set to their default value (H).

    :::{note}
    The labels for the digital inputs shown on this page will vary depending on the motor control mode selected on the "Drive Profile" page (see {numref}`sec:page_drive_profile`). {numref}`fig:conf_stepper_5` shows the configuration for the stepper motor, which includes inputs for the "step/direction" control mode.
    :::

- **Digital Outputs**: This section shows the digital outputs and allows you to select between normally open (H) or normally closed (L) for each. We will keep all outputs set to their default value (H).

- **Analog Inputs**: This section shows the analog inputs and allows you to set the supported value range from 0 V to 10 V or from -10 V to 10 V. In our case, we will use analog input AI 1 with -10 V to 10 V signals to control the speed of the brushless motor, as mentioned in {numref}`sec:axis_absolute_feedback`. Therefore, on the brushless motor controller, we will set the AI 1 option to ± 10 VDC. We will leave the AI 2 option unchanged, as we will not be using that input.

- **Digital Input Switching**: This parameter determines how the system interprets digital input signals. The available options are PNP and NPN:

  - **PNP** (sourcing): In the activated state, the input is raised to the voltage applied at X2.11. In the deactivated state, the input is grounded via a pull-down resistor. In this configuration, current flows from the output of the higher-level control system to the input of the igus® dryve D1.
  - **NPN** (sinking): In the activated state, the input is grounded. In the deactivated state, the input is raised to the voltage applied at X2.11 due to a pull-up resistor. In this configuration, current flows from the input of the igus® dryve D1 to the output of the higher-level control system.

    Since all inputs and outputs of the MESA boards are of the PNP (sourcing) type, we will leave this option set to the default value "PNP."
