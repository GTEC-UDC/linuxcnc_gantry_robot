# igus® dryve D1 Controllers

:::{note}
This section was taken from our LinuxCNC testbed project (<https://github.com/GTEC-UDC/linuxcnc_testbed>). It needs to be updated to reflect the gantry robot configuration.
:::

:::{important}
For the testbed development we used the igus® dryve D1 controllers with firmware version `dryve-D1-1-20220525` and their operating manual with version `3.0.1`.
:::

In this section, we will detail the configuration of the igus® dryve D1 controllers. To configure them, connect each controller to a PC via an Ethernet cable. If you do not know a controller's IP address, you can find it by powering on the device or reconnecting the Ethernet cable. In either case, the controller will sequentially display its IP address, digit by digit, on the seven-segment display located on its front panel.

Once connected, open a web browser and enter the IP address of the controller you wish to configure. This will grant access to the controller's web-based configuration interface. The following sections describe the controller's configuration parameters and the values to be applied for both the brushless and stepper motors. For more comprehensive information, it is recommended to consult the official controller manual.

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
