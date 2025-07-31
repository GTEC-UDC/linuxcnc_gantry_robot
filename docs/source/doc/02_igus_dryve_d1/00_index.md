# igus® dryve D1 Controllers

:::{important}
For the gantry robot development we used the igus® dryve D1 controllers with firmware version `dryve-D1-1-20240927` and their operating manual with version `3.1`.
:::

In this section, we will detail the configuration of the igus® dryve D1 controllers for our gantry robot. The robot uses 4 motors, each with its own controller:

- **X1 axis**: igus® MOT-EC-86-C-I-A brushless motor with 1000 {{PPR}} encoder and 10:1 reduction gear.
- **X2 axis**: identical to X1
- **Y axis**: identical to X1 and X2
- **Z axis**: igus® MOT-AN-S-060-035-060-M-C-AAAC stepper motor with 500 {{PPR}} encoder.

To configure each controller, connect it to a PC via an Ethernet cable. If you do not know a controller's IP address, you can find it by powering on the device or reconnecting the Ethernet cable. In either case, the controller will sequentially display its IP address, digit by digit, on the seven-segment display located on its front panel.

Once connected, open a web browser and enter the IP address of the controller you wish to configure. This will grant access to the controller's web-based configuration interface. The following sections describe the controller's configuration parameters and the values to be applied for both the brushless motors (X1, X2, Y) and the stepper motor (Z). For more comprehensive information, it is recommended to consult the official controller manual.

:::{toctree}
:maxdepth: 2
:caption: Table of Contents

01_start_page.md
02_motor_page.md
03_axis_page.md
04_communication_page.md
05_inputs_ouputs_page.md
06_drive_profile_page.md
07_oscilloscope_page.md
:::
