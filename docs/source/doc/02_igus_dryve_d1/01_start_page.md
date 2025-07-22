(sec:conf_start)=
# "Start" Page

The "Start" configuration page, shown in {numref}`fig:conf_stepper_1`, contains various general settings. Specifically, we will configure the following options for all the controllers:

- **Measuring system**: Metric, Millimeter
- **Movement type**: Rotary
- **Time units**: Seconds

:::{figure} images/config-stepper/01-start.png
:name: fig:conf_stepper_1

Initial configuration page of the stepper motor controller.
:::

:::{note}
We have configured the Movement type option as "Rotary," despite the motor driving a linear axis. This is because we do not require the controller to control the axis position, LinuxCNC will handle this. Our only requirement is for the controller to respond to the movement signals we transmit.
:::

Additionally, this page includes the following sections:

- **Configuration**: This section allows you to save the current controller configuration to a file and load a configuration from a file. Once the controller configuration is defined, it is recommended to use this functionality to save it.
- **Firmware**: This section enables updating the controller firmware. The "Search" button directs you to the URL for downloading the latest firmware version. The "Update" button allows you to load the firmware file from your disk to update the controller.
- **Password**: This section allows you to set a password for "Admin" and "Guest" users. These users can be activated or deactivated using their respective switches. If both users are deactivated (the default setting), the user interface is accessed with the "Admin" user. The "Guest" user can only be activated if the "Admin" user has been previously activated.
