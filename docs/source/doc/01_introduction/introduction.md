# Introduction

The gantry robot uses LinuxCNC as its control platform, integrated with Mesa Electronics interface boards and igus® dryve D1 motor controllers. It provides a displacement range of 5.3m (X) × 5.2m (Y) × 1m (Z), with a total work volume of approximately 6m (X) × 6m (Y) × 2m (Z). {numref}`fig:installation` shows a photograph of the gantry robot structure. The system diagram is shown in {numref}`fig:system_diagram`.

This system was developed from our LinuxCNC testbed (<https://github.com/GTEC-UDC/linuxcnc_testbed>). The system wiring diagram, detailing all components and their interconnections, is available in the {{project_url_link}}. Below, we detail the system's configuration, including the boards and components used.

:::{ext-figure} images/gantry_robot.*
:width-html: 75%
:name: fig:installation

Gantry robot structure.
:::

:::{ext-figure} images/system_diagram.*
:width-html: 75%
:name: fig:system_diagram

Gantry robot system diagram.
:::

## LinuxCNC

LinuxCNC, formerly known as the {{EMC}}, is a software system designed for the computer control of various machine tools, such as milling machines and lathes, as well as robots like PUMA and SCARA, and other computer-controlled machinery with up to nine axes. LinuxCNC is free, open-source software. Current versions are fully licensed under the [{{GPL}}](https://www.gnu.org/licenses/gpl.html) and [{{LGPL}}](https://gnu.org/licenses/lgpl.html).

In our system, LinuxCNC communicates with the igus® dryve D1 controllers via the MESA 7I96S and 7I77 boards. LinuxCNC is responsible for coordinating the operation of all motors, providing precise, real-time control over the system.

Detailed information on LinuxCNC's operation and configuration can be found in {numref}`sec:linuxcnc`.

## System Hardware

This system comprises the following key components:

### Main Components

- **Control Computer**: PC running LinuxCNC for real-time motor coordination

- **4 Motor Controllers** [igus® dryve D1](https://www.igus.eu/product/D1): igus® dryve D1 can be used for controlling stepper, DC, and brushless motors in industrial and automation applications. The igus® dryve D1 supports the following communication methods with control systems:

  - **CANopen**: A communication protocol widely used in industrial automation systems, built upon the CAN bus (ISO 11898) standard.
  - **Modbus TCP**: A communication protocol extensively employed in industrial applications for data transmission over Ethernet networks using the TCP protocol.
  - **Analog and Digital Signals**: In addition to network communication options, the igus® dryve D1 can receive analog and digital signals for direct control.

    In this system, we communicate with the igus® dryve D1 controllers using MESA 7I96S and 7I77 boards using digital and analog signals. This setup enables LinuxCNC to have precise, real-time control over the motors' operation.

### Interface Boards

- **Main Board** [MESA 7I96S](https://store.mesanet.com/index.php?route=product/product&product_id=374): This board is the primary hardware interface between LinuxCNC and the igus® dryve D1 controllers. It connects to the computer running LinuxCNC via an Ethernet connection. Its main functions include:

  - Controlling the stepper motor by sending step and direction signals to its designated igus® dryve D1 controller.
  - Receiving input signals from limit switches.

- **Expansion Board** [MESA 7I77](https://store.mesanet.com/index.php?route=product/product&product_id=120): This board connects to the 7I96S board via a 25-pin flat cable. Its primary functions are:

  - Controlling the brushless motor by sending an analog speed signal to its corresponding igus® dryve D1 controller.
  - Receiving position feedback signals from motor encoders.
  - Receiving warning and error signals from the controllers.
  - Receiving the emergency stop signal when the emergency stop switch is activated.

### Motors and Actuators

- **X-axis Motors**: 2 x [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) - NEMA 34 brushless with 1000 PPR encoder

- **Y-axis Motor**: 1 x [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) - NEMA 34 brushless with 1000 PPR encoder

- **Z-axis Motor**: 1 x [igus® MOT-AN-S-060-035-060-M-C-AAAC](https://www.igus.eu/product/motors-and-gears) - NEMA 24 stepper with 500 PPR encoder

### Safety Systems and Sensors

- **Emergency Stop Switch**: This switch has both a normally closed and a normally open contact.

- **Limit Sensors**: 4 x igus® inductive sensors for position limit detection

- **LED Indicators**: Custom indicators with red, yellow, and green LEDs, which provide a visual display of the system's status.

### Power Supply

- **48V Power Supplies**: 3 x MEAN WELL SDR-960 for brushless motor power
- **24V Power Supply**: 1 x MEAN WELL SDR-240 for stepper motor power
- **Additional 24V Power Supply**: For igus® dryve D1 logic and MESA 7I77 field power
- **5V Power Supply**: MEAN WELL MDR-20-5 for MESA 7I77 field I/O logic

### Linear Units

The system is built with igus® self-lubricating linear units that enable lifetime operation of moving parts without external lubrication.

## Calibration System

This project includes the following calibration components:

- **Custom LinuxCNC kinematic module `calibxyzkins`** in `linuxcnc/components/linuxcnc_calibrated_xyz_kins`: enables real-time positioning error compensation
- **Calibration analysis software** in the `calibration/` folder: Python-based tools for processing OptiTrack data and generating calibration parameters

This solution enables the gantry robot to achieve sub-centimeter precision throughout the entire working volume of 5.3m × 5.2m × 1m.
