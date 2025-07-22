(sec:linuxcnc_configuration)=
# LinuxCNC Configuration

As noted in {numref}`sec:linuxcnc_intro_config`, a LinuxCNC configuration comprises several files, requiring at least one INI file and one {{HAL}} file. The following sections detail the configuration of both file types, using the `mesa_7i96s_7i77_xy` configuration as an example.

(sec:linuxcnc_configuration_ini)=
## INI Configuration

### .ini Configuration File Format

An `.ini` file is a plain text file used for configuring applications and programs. It has a simple structure consisting of sections and key-value pairs. The basic syntax of an `.ini` file is as follows:

- **Sections**: Sections serve to organize keys and values. Each section begins with its name enclosed in square brackets, followed by zero or more key-value pairs belonging to that section. The syntax for a section is:

    ```ini
    [section_name]
    ```

- **Keys and Values**: Within each section, keys and their corresponding values can be defined. Keys are identifiers used to access associated values. The syntax for a key-value pair is:

    ```ini
    key = value
    ```

    Keys can contain letters and underscores (`_`). Values can be text strings, integers, or floating-point numbers.

- **Comments**: Comments begin with a semicolon (`;`) or a hash symbol (`#`). For example:

    ```ini
    ; This is a comment
    # This is also a comment
    ```

### Example: `mesa_7i96s_7i77_xy.ini` Configuration File

Below are the different sections of the `mesa_7i96s_7i77_xy.ini` configuration file, with comments explaining the purpose of each parameter. Note that not all available parameters are specified in some sections. For a complete list of parameters and their documentation, consult the LinuxCNC user manual {cite}`linuxcncdoc`.

- **EMC Section**: General configuration.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 1-12
    :lineno-match:
    :::

- **DISPLAY Section**: User interface configuration. The available options may depend on the specific user interface used. In this case, we are using the AXIS user interface.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 14-64
    :lineno-match:
    :::

- **TASK Section**: LinuxCNC task controller configuration. The task controller is responsible for communicating with the user interface, the motion planner, and the G-code interpreter. Currently, `milltask` is the only task controller available. For more information, consult the LinuxCNC user manual {cite}`linuxcncdoc` and the `milltask` man page, also available at <http://linuxcnc.org/docs/devel/html/man/man1/milltask.1.html>.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 67-74
    :lineno-match:
    :::

- **RS274NGC Section**: RS274NGC (G-code) interpreter configuration.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 77-84
    :lineno-match:
    :::

- **EMCMOT Section**: Motion controller configuration. The `EMCMOT` and `SERVO_PERIOD` parameters are not directly used by LinuxCNC but are used to configure the motion control module in the {{HAL}} file (see {numref}`sec:linuxcnc_configuration_hal`).

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 87-100
    :lineno-match:
    :::

- **{{HAL}} Section**: {{HAL}} configuration.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 103-117
    :lineno-match:
    :::

- **HALUI Section**: HALUI (HAL-based user interface) configuration. The only available option is `MDI_COMMAND`, which allows MDI commands to be executed via {{HAL}} signals. In our case, this section is left empty.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 120-126
    :lineno-match:
    :::

- **KINS Section**: Kinematics configuration.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 129-137
    :lineno-match:
    :::

- **APPLICATIONS Section**: LinuxCNC allows applications to be launched at startup. These applications must be specified within the `APPLICATIONS` section using the `APP` option, which can be used multiple times. Applications will be launched either at the beginning, before the graphical interface starts, or after a delay specified by the `DELAY` option.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 140-144
    :lineno-match:
    :::

- **TRAJ Section**: Trajectory planner configuration.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 147-164
    :lineno-match:
    :::

- **EMCIO Section**: Input/output controller configuration. This controls input/output tasks such as coolant, tool changes, and emergency stops.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 167-174
    :lineno-match:
    :::

- **AXIS\_\<i\> Section**: Configuration for axis *\<i\>*. Possible values for *\<i\>* include `X`, `Y`, `Z`, `A`, `B`, `C`, `U`, `V`, and `W`. An example of the X-axis configuration is provided below; the Y-axis configuration is similar.

    :::{important}
    When configuring the robot's limits (`MIN_LIMIT` and `MAX_LIMIT` parameters), it is advisable to leave some margin beyond the desired workspace. If the robot is commanded to position itself at one of the limits, it can easily exceed that limit slightly. For example, if you want your robot to operate on the X-axis between X = 0 and X = 200, you could configure `MIN_LIMIT = -5` and `MAX_LIMIT = 205`.
    :::

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 177-190
    :lineno-match:
    :::

- **JOINT\_\<n\> Section**: Configuration for joint (motor) *\<n\>*, where *\<n\>* is the joint number, ranging from 0 to (*\<num_joints\>* $-$ 1). The value of *\<num_joints\>* is set in the `JOINTS` option of the `KINS` section.

    For machines with Cartesian geometries, such as gantry robots, LinuxCNC includes the `trivkins` kinematics module. With this module, by default, there is a 1:1 correspondence between the axis coordinate letter and the joint number, i.e., JOINT_0 = X, JOINT_1 = Y, ..., JOINT_8 = W.

    The `trivkins` module accepts the `coordinates` parameter to specify the association of axis coordinate letters with the joint number. For example, with the parameter `coordinates=XZ`, JOINT_0 will be assigned to X and JOINT_1 to Z. In this parameter, the same axis letter can be specified multiple times, allowing multiple joints to be assigned to the same axis. In this case, it is also necessary to use the `kinstype=B` parameter. For instance, with the parameters `coordinates=XX` and `kinstype=B`, both JOINT_0 and JOINT_1 will be assigned to X.

    For more information about the `trivkins` kinematics module, consult the `kins` man page, also available at <http://linuxcnc.org/docs/devel/html/man/man9/kins.9.html>.

    :::{important}
    Both the joint and axis configurations include `MAX_VELOCITY`, `MAX_ACCELERATION`, `MIN_LIMIT`, and `MAX_LIMIT` parameters. When the robot is not homed, LinuxCNC uses the parameters from the joint sections; however, once the robot is homed, it uses the parameters from the axis sections.
    :::

    The following code shows the configuration of joint 1 (X-axis), which corresponds to the stepper motor. The parameters specified below the comment "Custom configurations for the HAL file" are not directly used by LinuxCNC; they are used to configure the motor parameters in the {{HAL}} file (see {numref}`sec:linuxcnc_configuration_hal`).

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 193-299
    :lineno-match:
    :::

    The following code shows the configuration of joint 2 (Y-axis), which corresponds to the brushless motor. As before, the parameters specified below the comment "Custom configurations for the HAL file" are not directly used by LinuxCNC; they are used to configure the motor parameters in the {{HAL}} file (see {numref}`sec:linuxcnc_configuration_hal`). These parameters differ from the previous ones because now a brushless motor is used.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 318-409
    :lineno-match:
    :::

(sec:linuxcnc_configuration_hal)=
## {{HAL}} Configuration

{{HAL}} is a fundamental component of LinuxCNC, serving as an interface between the machine's software and hardware. It provides the infrastructure for communication among the system's numerous software and hardware components. The {{HAL}} layer is composed of components that:

- Are interconnected, processing incoming data and providing outputs to other components (e.g., the motion planning algorithm instructs the motors on their movement).
- Possess the ability to communicate with hardware.
- Always run periodically in one of the following ways:
  - As real-time components, either with an execution frequency of a few microseconds (e.g., to advance a stepper motor or read an encoder) or with a frequency less than one millisecond (e.g., to adjust the planning of subsequent movements to complete a G-code instruction).
  - As non-real-time user-space components, which can be interrupted or delayed if the rest of the system is busy or overloaded.

The {{HAL}} components included with LinuxCNC are listed in the user manual {cite}`linuxcncdoc`, also available at <http://linuxcnc.org/docs/stable/html/hal/components.html>. Additionally, each component has its own man page.

### Basic Concepts

- **Pins and Signals**: {{HAL}} is based on the same principles used to design electrical circuits and hardware systems, employing "pins" and "signals" to represent the flow of data between {{HAL}} modules or components. In summary:

  - Pins can carry boolean, float, and signed or unsigned integer values.
  - Pins have a direction: input (IN), output (OUT), or input/output (I/O).
  - A signal identifies a connection between pins.

    {numref}`fig:hal_circuit_concept` from the LinuxCNC documentation {cite}`linuxcncdoc` illustrates the concepts of components, pins, and signals in {{HAL}}. In the figure, pin `pin3-out` of `component.0` connects to pins `pin3-in` and `pin4-in` of `component.1` (via the `signal-red` signal), and pin `pin1-out` of `component.1` connects to pin `pin1-in` of `component.0` (via the `signal blue` signal).

    :::{figure} images/linuxcnc/hal_circuit_concept.png
    :name: fig:hal_circuit_concept

    {{HAL}} Concept --- Connection as electrical circuits. Source: LinuxCNC documentation {cite}`linuxcncdoc`.
    :::

- **Parameters**: {{HAL}} components can have parameters, which are input or output settings not connected to any other component. There are two types of parameters:

  - **Input parameters**: Values that the user can adjust and that remain fixed once configured.
  - **Output parameters**: Values that cannot be adjusted by the user. They allow for internal signals to be monitored.

- **Functions**: Each {{HAL}} component has one or more functions that must be executed to perform the component's task. For these functions to be executed, they must be added to a thread.

- **Threads**: Threads enable {{HAL}} component functions to be executed at specific time intervals. When a thread is created, the time interval at which its assigned functions will be executed is specified. Subsequently, the functions of the {{HAL}} components can be added to the thread to be executed in order at the thread's defined time interval.

### Interaction with {{HAL}} and Commands

{{HAL}} does not interact directly with the user. LinuxCNC provides various interfaces to configure or interact with {{HAL}}:

- From `.hal` files.
- From the command line using the `halcmd` command.
- From Python scripts.
- From C/C++ programs.

Configuration or interaction with {{HAL}} using any of these interfaces is performed through commands. The complete list of commands is detailed in the `halcmd` man page, also available at <http://linuxcnc.org/docs/html/man/man1/halcmd.1.html>. The most relevant commands are:

:::{note}
Generally, each command must be specified on a single line. If a command needs to be split across multiple lines, a backslash (`\`) character can be used to indicate that the line continues to the next. The backslash must be the last character before the new line.
:::

- `loadrt`: Loads a {{HAL}} real-time component into the system. The basic syntax of the `loadrt` command is:

    ```text
    loadrt <component> <options>
    ```

    where `<component>` is the name of the component and `<options>` are the component options. For example:

    ```hal
    loadrt mux4 count=1
    ```

- `addf`: Adds a function to a real-time thread. The syntax of the `addf` command is:

    ```text
    addf <function> <thread>
    ```

    where `<function>` is the name of the function and `<thread>` is the thread to which it will be added. For example:

    ```hal
    addf mux4.0 servo-thread
    ```

- `loadusr`: Loads a non-real-time {{HAL}} component into the system. Non-real-time components are separate processes that can optionally communicate with other {{HAL}} components via pins and parameters. Real-time components cannot be loaded into non-real-time space. The syntax of the `loadusr` command is:

    ```text
    loadusr [<flags>] <command>
    ```

    where `<command>` is the program command to be executed and `<flags>` can be one or more of the following options:

  - `-i`: Ignore the program's return value (with `-w`).
  - `-w`: Wait for the program to finish.
  - `-W`: Wait for the component to be ready. It is assumed that the component will have the same name as the first argument of the command.
  - `-Wn``<name>`: Wait for the component to be ready and assign it the name `<name>`. This is only applicable if the component has the `-n` option to assign a name.

    For example:

    ```hal
    loadusr -Wn spindle gs2_vfd -n spindle
    ```

- `net`: Creates a connection between a signal and one or more pins. The syntax is as follows:

    ```text
    net <signal> <pin>
    ```

    where `<signal>` is the name of the signal and `<pin>` is the name of a pin. If the signal does not exist, a new signal is created. The command also allows the use of the words `<=`, `=>`, and `<=>`, separated by a space from the pin names, to indicate the direction of the signals between pins. These words are ignored by the command and merely serve to facilitate readability.

    The following rules must be met to connect a pin to a signal:

  - An input (IN) pin can always be connected to a signal.
  - An input/output (I/O) pin can be connected unless there is an output (OUT) pin on the signal.
  - An output (OUT) pin can be connected only if there are no other output (OUT) or input/output (I/O) pins on the signal.

    The same signal name can be used in multiple `net` commands to connect additional pins, provided the above rules are respected.

    Examples:

    - ```hal
       net home-x joint.0.home-sw-in <= parport.0.pin-11-in
       ```

       where `home-x` is the signal name, `joint.0.home-sw-in` is an input (IN) pin, `<=` is the optional direction arrow (ignored by the command), and `parport.0.pin-11-in` is an output (OUT) pin.

       This example can also be equivalently defined in {{HAL}} by two `net` commands:

       ```hal
       net home-x <= parport.0.pin-11-in
       net home-x => joint-0.home-sw-in
       ```

       :::{note}
       As seen in this example, although the second pin's name has the `-in` suffix, {{HAL}} treats it as an output pin. Therefore, when configuring pin connections in {{HAL}}, always refer to how the pin is configured in {{HAL}}, not just its name.
       :::

    - ```hal
      net xStep stepgen.0.out => parport.0.pin-02-out parport.0.pin-08-out
      ```

      where `xStep` is the signal name, `stepgen.0.out` is an output pin, and `parport.0.pin-02-out` and `parport.0.pin-08-out` are input pins.

      This example can also be defined in {{HAL}} by two `net` commands as follows:

      ```hal
      net home-x <= stepgen.0.out
      net home-x => parport.0.pin-02-out parport.0.pin-08-out
      ```

- `setp`: Sets the value of a pin or parameter. Valid values depend on the pin or parameter's data type. The syntax of this command is:

    ```text
    setp <name> <value>
    ```

    where `<name>` is the name of the pin or parameter and `<value>` is the value to which it is to be set. The command will fail if `<name>` does not exist as a pin or parameter, if it is a read-only parameter, if it is an output (OUT) pin, if it is a pin that is already connected to a signal, or if `<value>` is not a valid value for the pin or parameter's data type.

- `sets`: Sets the value of a signal. The syntax is:

    ```text
    sets <signal> <value>
    ```

    where `<signal>` is the name of the signal and `<value>` is the value to which it is to be set. The command will fail if `<signal>` does not exist as a signal, if the signal is already connected to an output (OUT) pin, or if `<value>` is not a valid value for the signal's data type.

- `unlinkp`: Unlinks a pin from its connected signal. The syntax of the command is:

    ```hal
    unlinkp <name>
    ```

    where `<name>` is the name of the pin. If the pin does not have a connected signal, nothing happens. The command will fail if `<name>` does not exist as a pin.

### .hal File Format

A `.hal` file is a plain text file containing {{HAL}} commands. Comments can be included by starting lines with the hash symbol (`#`). Options from the `.ini` file can be accessed with the syntax `[<section>]<option>`, where `[<section>]` is the section name in square brackets and `<option>` is the corresponding option name within that section.

### Example: `mesa_7i96s_7i77_xy.hal` Configuration File

As noted in {numref}`sec:linuxcnc_intro_config`, a LinuxCNC configuration includes at least one `.ini` file and one `.hal` file. Below is the `mesa_7i96s_7i77_xy.hal` configuration file, corresponding to the `mesa_7i96s_7i77_xy.ini` file detailed in {numref}`sec:linuxcnc_configuration_ini`. Unlike the `.ini` format, the `.hal` format does not have a formal section syntax; however, for clarity, the file is presented below divided into different parts.

- **Load modules, add functions to threads, and other initial configurations**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 1-54
    :lineno-match:
    :::

- **X-axis configuration (joint 0, stepper motor)**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 57-120
    :lineno-match:
    :::

- **Y-axis configuration (joint 1, brushless motor)**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: hal
    :lines: 123-179
    :lineno-match:
    :::

- **Other configurations**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 182-265
    :lineno-match:
    :::

## {{HAL}} Tools

Several {{HAL}} tools are available for real-time visualization and diagnosis of pin states. The most notable ones are described below; for a complete list of tools, consult the LinuxCNC user manual {cite}`linuxcncdoc`.

### Halcmd

`halcmd` is a command-line tool for interacting with {{HAL}}. When `halcmd` is executed, the following command line will appear:

```text
halcmd:
```

This prompt allows you to enter and execute {{HAL}} commands. Besides the commands detailed previously in {numref}`sec:linuxcnc_configuration_hal`, other commands such as `show`, `list`, or `save` can be very useful. These commands enable printing various elements defined in {{HAL}}, such as pins, parameters, threads, etc. The complete list of commands is detailed in the `halcmd` man page, also available at <http://linuxcnc.org/docs/html/man/man1/halcmd.1.html>.

### Halshow

`halshow` is a graphical tool that allows viewing and monitoring {{HAL}} components such as pins, parameters, signals, and functions. This tool is shown in Figures {numref}`%s <fig:halshow_show>` and {numref}`%s <fig:halshow_watch>`. The tool has the following main elements:

- A tree view displaying {{HAL}} pins, parameters, signals, functions, etc. This view is located on the left side of the window, as seen in Figures {numref}`%s <fig:halshow_show>` and {numref}`%s <fig:halshow_watch>`.
- A text input field for executing {{HAL}} commands, located at the bottom, as shown in Figures {numref}`%s <fig:halshow_show>` and {numref}`%s <fig:halshow_watch>`.
- A "SHOW" tab where information about the selected element in the tree view is displayed, as shown in {numref}`fig:halshow_show`.
- A "WATCH" tab where you can monitor and set values of {{HAL}} pins or parameters. Elements can be added here by clicking on them in the tree view, as shown in {numref}`fig:halshow_watch`.
- A "SETTINGS" tab with various options such as refresh interval or display format of parameters.

The {menuselection}`File` menu allows saving monitored elements from the "WATCH" tab to a file, as well as loading an existing list of elements to monitor from a file.

You can open the Halshow tool from the AXIS graphical interface by clicking on {menuselection}`Machine --> Show Hal Configuration`.

:::{figure} images/linuxcnc/halshow_show.png
:name: fig:halshow_show
:width: 70%

Halshow tool showing the "SHOW" tab.
:::

:::{figure} images/linuxcnc/halshow_watch.png
:name: fig:halshow_watch
:width: 70%

Halshow tool showing the "WATCH" tab.
:::

### Halscope

`halscope` is a graphical tool that provides an oscilloscope for {{HAL}}. It allows capturing and displaying the values of pins, signals, and parameters over a period of time. This tool is shown in {numref}`fig:halscope`. The {menuselection}`File` menu allows saving the current configuration or opening a previously saved configuration. When `halscope` is closed, the configuration is automatically saved to the `autosave.halscope` file.

:::{figure} images/linuxcnc/hal_oscilloscope.png
:name: fig:halscope

Halscope tool showing the values of `joint.0.motor-pos-cmd` (motor position commanded by LinuxCNC) and `joint.0.motor-pos-fb` (motor position read from the encoder) over time.
:::

You can open the Halscope tool from the AXIS graphical interface by clicking on {menuselection}`Machine --> Hal scope`.

### Halreport

`halreport` is a command-line tool that generates a report on {{HAL}} connections. The command's help output is as follows:

```text
Usage:
    halreport -h | --help (this help)
or
    halreport [outfilename]
```

The generated report displays all signal connections and indicates potential issues. The information included in the report, among other things, is:

- System description and kernel version.
- Signals and their connected output, input, and input/output pins.
- Functions, threads, and `addf` commands corresponding to each pin.
- Real names for pins that use aliases.
- Signals without an output.
- Signals without inputs.
- Functions not added to threads.
- Warnings about components marked as obsolete.

## Ladder Logic Programming

LinuxCNC includes the ClassicLadder component, a free implementation of a ladder interpreter published under the [{{LGPL}}](https://gnu.org/licenses/lgpl.html).

Ladder logic, or the ladder programming language, is a method for drawing electrical logic diagrams. Originally conceived to describe control systems using relays, this approach has become a widely used graphical language for programming {{PLC}} devices. It derives its name from the fact that programs in this language resemble ladders, with two vertical rails and a series of horizontal rungs between them.

To use ClassicLadder, you must load the `classicladder_rt` real-time module in {{HAL}} and add the `classicladder.0.refresh` function to the `servo-thread` thread using the following commands:

```hal
loadrt classicladder_rt addf classicladder.0.refresh servo-thread
```

Once this is done, you can open the ClassicLadder graphical interface with the system command `classicladder`, or from the AXIS interface by clicking on {menuselection}`File --> Ladder Editor...`. The ClassicLadder graphical interface allows you to create ladder logic programs, as well as view the logical status of the different program components. This interface is composed of several windows, as shown in {numref}`fig:classicladder`.

:::{figure} images/linuxcnc/linuxcnc_ladder_editor.png
:name: fig:classicladder

ClassicLadder graphical interface.
:::

In our testbed setup, ladder logic has been used to program the operation of the LED indicator panel. The program created with ClassicLadder has been saved in the `myladder.clp` file. To use it in LinuxCNC, it can be loaded with the following {{HAL}} command:

```hal
loadusr classicladder myladder.clp -nogui
```

The LinuxCNC user manual {cite}`linuxcncdoc` includes a detailed guide to ClassicLadder. Another good introduction to ClassicLadder is "The Feral Engineer"'s "Classicladder tutorials" series on YouTube: <https://www.youtube.com/playlist?list=PLTYvfbjLClpfAfJSGhZUecgXFwVPY5e09>.
