# Introduction to LinuxCNC

LinuxCNC is a highly customizable suite of applications for controlling {{CNC}} machines, 3D printers, robots, and other automated devices. It is capable of providing coordinated control of up to nine axes of motion. LinuxCNC comprises several key components integrated into a complete system {cite}`linuxcncdoc`:

- A {{GUI}}, which serves as the primary interface between the operator, the software, and the {{CNC}} machine itself.
- The {{HAL}}, which enables the linking of signals from the external environment with LinuxCNC and vice versa.
- High-level modules that coordinate the generation, execution, and motion control of the {{CNC}} machine, specifically the motion controller, the input/output controller, and the task executor.

This document provides only a brief overview of LinuxCNC; for more detailed information, it is recommended to consult the LinuxCNC user manual {cite}`linuxcncdoc`, which comprehensively describes how to use the software. On a system with LinuxCNC installed, the manual can be accessed by clicking on {menuselection}`Applications menu --> CNC --> Documentation`.

## Running LinuxCNC

You can run LinuxCNC by clicking on {menuselection}`Applications menu --> CNC --> LinuxCNC` or by using the `linuxcnc` command. Its usage is shown in {numref}`lst:linuxcnc_help`.

:::{code-block} text
:name: lst:linuxcnc_help
:caption: Usage of the linuxcnc command

linuxcnc: Run LinuxCNC

Usage:
  $ linuxcnc -h
    This help

  $ linuxcnc [Options]
    Choose the configuration INI file graphically

  $ linuxcnc [Options] path/to/your_ini_file
    Name the configuration INI file using its path

  $ linuxcnc [Options] -l
    Use the previously used configuration INI file

Options:
    -d: Turn on "debug" mode
    -v: Turn on "verbose" mode
    -r: Disable redirection of stdout and stderr to ~/linuxcnc_print.txt and
        ~/linuxcnc_debug.txt when stdin is not a tty.
        Used when running linuxcnc tests non-interactively.
    -l: Use the last-used INI file
    -k: Continue in the presence of errors in HAL files
    -t "tpmodulename [parameters]"
            specify custom trajectory_planning_module
            overrides optional INI setting [TRAJ]TPMOD
    -m "homemodulename [parameters]"
            specify custom homing_module
            overrides optional INI setting [EMCMOT]HOMEMOD
    -H "dirname": search dirname for HAL files before searching
                  INI directory and system library:
                  /home/git/linuxcnc-dev/lib/hallib
Note:
    The -H "dirname" option may be specified multiple times
:::

If you click on {menuselection}`Applications menu --> CNC --> LinuxCNC` or run the `linuxcnc` command without specifying a configuration file, the LinuxCNC configuration selector will open, as shown in {numref}`fig:linuxcnc_conf_selector`.

:::{figure} images/linuxcnc/configuration_selector.png
:name: fig:linuxcnc_conf_selector

LinuxCNC configuration selector.
:::

In the configuration selector, available configurations are displayed in a tree structure, reflecting their directory structure, with two initial nodes:

- **My configurations**: User-defined configurations, stored in the `~/linuxcnc/configs` folder.
- **Sample configurations**: Example configurations provided by default with LinuxCNC, stored in `/usr/share/linuxcnc/configs`.

To start LinuxCNC with a configuration, simply double-click on it or select it and press the {guilabel}`OK` button.
If you check the "Create Desktop Shortcut" box, a desktop icon will also be created to directly launch LinuxCNC with the respective configuration. Finally, if the configuration is one of the *Sample configurations*, LinuxCNC will prompt the user to copy it to the `~/linuxcnc/configs` folder, allowing for later modification. If the user accepts, the configuration will subsequently appear under the *My configurations* category.

(sec:linuxcnc_intro_config)=
## Configuration Files

A LinuxCNC configuration typically consists of several files. For example, considering a configuration folder named "robot," a typical setup would include the following files:

- `robot.ini`: The main LinuxCNC configuration file. This defines parameters such as speeds, accelerations, axis configuration, and other important settings.
- `robot.hal`: The main {{HAL}} file. This contains the configuration for mapping LinuxCNC signals with the system's hardware interface, defining how physical components relate to logical signals within LinuxCNC. When LinuxCNC starts, this file is read and processed before the {{GUI}} is loaded.
- `robot_custom.hal` (optional): LinuxCNC allows for specifying multiple `.hal` files. This file would contain additional {{HAL}} configurations.
- `robot_postgui.hal` (optional): {{HAL}} configurations that are executed after the {{GUI}} has loaded. This can include display configurations, such as linking a LinuxCNC signal to a {{GUI}} element to display its value.
- `rs274ngc.var` (optional): Parameters for the G-code interpreter (see {numref}`sec:linuxcnc_intro_gcode`) that will persist across different LinuxCNC executions.
- `tool.tbl` (optional): The tool table configuration. This is used to define tools and their properties, such as dimensions and offsets.

{numref}`sec:linuxcnc_configuration` shows an example of a LinuxCNC configuration.

(sec:linuxcnc_intro_gcode)=
## G-code Language

G-code is the most widely used programming language in {{CNC}}. A G-code program consists of a series of instructions that command the machine on how to move or perform specific operations. G-code has its origins in the early days of industrial automation, developed as a standard method for communicating instructions to {{CNC}} machines in the 1950s and 60s. It was standardized as RS-274 by the {{EIA}} in 1963, with its final revision standardized as RS-274-D in 1979 and as ISO 6984 in 1982. Subsequently, numerous implementations and derived standards emerged, developed by both public and private entities.

In LinuxCNC, G-code is the language used to control machine movement. Specifically, the version implemented by LinuxCNC is based on the RS274/NGC language developed by the {{NIST}} {cite}`RS274NGC`. The LinuxCNC documentation extensively details the G-code language {cite}`linuxcncdoc{section G-code Programming}`. Some example G-code commands are presented below:

- `G0 X10 Y5 Z3`: Rapid linear movement to coordinates X=10, Y=5, and Z=3.
- `F100`: Sets the feed rate to 100 units per minute.
- `G1 X20 Y15`: Linear movement to coordinates X=20 and Y=15 at the current feed rate.
- `G1 F100 X20 Y15`: Sets the feed rate to 100 units per minute and then moves linearly to coordinates X=20 and Y=15.
- `G2 X30 Y10 I5 J0`: Clockwise circular movement with center at X=5, Y=0 and a radius of 5 units.
- `G3 X40 Y5 I2 J3`: Counter-clockwise circular movement with center at X=2, Y=3 and a radius of 5 units.
- `M3 S1000`: Activates the spindle at 1000 rpm in a clockwise direction.
- `M5`: Deactivates the spindle.

These are just a few basic examples of G-code commands. In practice, G-code programs typically consist of multiple lines, each containing a command, and like any other programming language, they can define variables, subroutines, and incorporate loops or flow control.

(sec:linuxcnc_modes_of_operation)=
## Modes of Operation

LinuxCNC offers three distinct modes of operation, each designed for a specific purpose: manual, automatic, and {{MDI}}. These modes define how commands are entered and executed:

- In manual mode, commands are entered individually. These commands represent direct actions, such as "activate coolant" or "move X-axis to 25 inches per minute." In graphical interfaces, manual control is typically handled via buttons or keyboard shortcuts.
- Automatic mode enables the full execution of G-code programs stored in files. A single command can load and execute an entire file.
- MDI mode allows for the execution of individual G-code commands.

It is important to note that certain commands, such as *Abort*, *Emergency Stop*, and *Feed Rate Override*, can be used in all modes.

## Graphical Interface

LinuxCNC provides various graphical interfaces for controlling {{CNC}} machines. The specific interface to use is configured within the `.ini` file. A comprehensive list of available graphical interfaces, along with images and examples, can be found in the LinuxCNC user manual {cite}`linuxcncdoc`.

One of the most popular graphical interfaces is "AXIS," designed for control via keyboard and mouse. This graphical interface is shown in {numref}`fig:linuxcnc_gui_axis_estop`. Additionally, LinuxCNC also offers the "HALUI" interface, a purely hardware-based interface that allows controlling the {{CNC}} machine using only physical buttons and switches.

:::{figure} images/linuxcnc/linuxcnc_gui_axis.png
:name: fig:linuxcnc_gui_axis_estop

LinuxCNC "AXIS" graphical interface.
:::

In our testbed setup, we have considered the AXIS graphical interface. The window of this interface, as shown in {numref}`fig:linuxcnc_gui_axis_estop`, contains the following elements:

- A display area with two tabs:

  - "Preview" tab: Shows the position of the point controlled by the machine. Subsequently, it will display the path traced by the machine.
  - "DRO" (Digital Readout) tab: Shows the current position and all active offsets.

- A menu bar and a toolbar that enable various actions.

- "Manual Control" tab: Allows for manual machine movement.

- "MDI" (Manual Data Input) tab: Allows entering G-code programs manually, line by line.

- "Feed Override": Allows scaling the speed of programmed movements.

- "Rapid Override": Allows scaling the speed of rapid movements (e.g., G-code `G0` commands).

- "Jog Speed": Allows configuring the "jog" speed, which is the speed when the robot is controlled with the {guilabel}`+` and {guilabel}`-` controls of the "Manual Control" tab.

- "Max Velocity": Allows limiting the maximum speed of all programmed movements.

- "Active G-codes": Shows the modal G-codes that are currently active. Some of the most relevant ones displayed in {numref}`fig:linuxcnc_gui_axis_estop` are:

  - `G17`: Sets the machine's work plane to XY.
  - `G21`: Sets the units of measurement to millimeters.
  - `G90`: Sets the absolute coordinate mode.
  - `G94`: Sets the feed rate to be interpreted in units per minute.
  - `F0`: Sets the feed rate to zero.

    Detailed information on G-codes can be found in the LinuxCNC user manual {cite}`linuxcncdoc{section G-Codes}`, also available at <https://linuxcnc.org/docs/html/gcode/g-code.html>.

- A text display area that shows the loaded G-code file.

- A status bar that shows various useful data:

  - Machine status: "ESTOP" (emergency stop), "OFF" (off), or "ON" (on).
  - Tool currently inserted.
  - Displayed position: "relative" (showing all offsets), or "actual" (showing feedback position).
