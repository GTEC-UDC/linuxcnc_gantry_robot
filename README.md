# LinuxCNC Gantry Robot System

A large high-precision 3-axis gantry robot system using [LinuxCNC](https://www.linuxcnc.org), integrated with [Mesa Electronics](https://store.mesanet.com/) interface cards and [igus® dryve D1](https://www.igus.eu/product/D1) motor controllers.

The system was developed from our [LinuxCNC motor control testbed](https://github.com/GTEC-UDC/linuxcnc_testbed), which ensured the main components of the system were able to work reliably.

The repository includes a **custom calibration solution** that leverages an existing [OptiTrack](https://optitrack.com/) motion capture system in the installation room to measure and compensate for errors in the gantry movement. Using this solution the gantry robot can achieve sub-centimeter precision across the entire work envelope.

<div align="center">

[![LinuxCNC](https://img.shields.io/badge/Control-LinuxCNC-blue.svg)](https://linuxcnc.org/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-limegreen.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Documentation](https://img.shields.io/badge/docs-sphinx-blue.svg)](docs/)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://python.org)

<img src="assets/gantry_robot.jpg" style="width:100%; max-width:700px;" alt="Gantry Robot System"/>

</div>

## Key Features

- **3-Axis Control**: X, Y, Z linear axes.
- **Large Work Envelope**: 5.3m (X) × 5.2m (Y) × 1m (Z) working volume.
- **Real-time Coordination**: Precise real-time motion using LinuxCNC with MESA interface cards and igus® dryve D1 motor controllers.
- **Closed Loop Control**: High-precision encoder feedback for accurate positioning using closed loop control.
- **Visual Status Indicators**: Custom LED status indicators.
- **Positioning calibration**: Software to analyze OptiTrack measurements and custom LinuxCNC kinematics module for compensation of positioning errors.
- **Heavy Duty**: Built with igus® self-lubricating linear units enabling lifelong operation of the moving parts without external lubrication.

## Documentation

> [!NOTE]
> The technical documentation is under development.

The following documentation is provided in this repository:

- **Technical Documentation**: [Sphinx](https://www.sphinx-doc.org) sources of the system documentation and setup guide in [docs/](docs/). You can build the HTML version of the documentation with the following commands:

  ```bash
  cd docs
  uv venv && uv sync && source .venv/bin/activate
  make html
  ```

- **Electrical Installation**: KiCAD electrical schematics in [electrical_installation/](electrical_installation/).

## Positioning calibration

The gantry robot can be calibrated to compensate for positioning errors using an existing OptiTrack motion capture system in the installation room. For this, the repository provides the following software:

- **Custom `calibxyzkins` LinuxCNC Kinematics Module** in [linuxcnc/components/linuxcnc_calibrated_xyz_kins/](linuxcnc/components/linuxcnc_calibrated_xyz_kins/): compensates for the positioning errors in real-time
- **Calibration Analysis Software** in [calibration/](calibration/): Python-based tools for processing the OptiTrack data and generating the calibration parameters

## Hardware Components

| Component | Model | Quantity | Function |
|-----------|-------|----------|----------|
| **Control Computer** | PC running [LinuxCNC](https://www.linuxcnc.org) | 1 | Real-time motor coordination |
| **Motor Controllers** | [igus® dryve D1](https://www.igus.eu/product/D1) | 4 | Individual motor control |
| **Main Interface** | [MESA 7I96S](https://store.mesanet.com/index.php?route=product/product&product_id=374) | 1 | Ethernet-LinuxCNC bridge and stepper motor control |
| **I/O Expansion** | [MESA 7I77](https://store.mesanet.com/index.php?route=product/product&product_id=120) | 1 | Analog control for brushless motors and I/O signals |
| **X-Axis Motor** | [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) | 2 | NEMA 34 brushless with 1000 PPR encoder |
| **Y-Axis Motor** | [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) | 1 | NEMA 34 brushless with 1000 PPR encoder |
| **Z-Axis Motor** | [igus® MOT-AN-S-060-035-060-M-C-AAAC](https://www.igus.eu/product/MOT-AN-S-060-035-060-M-C-AAAC) | 1 | NEMA 24 stepper with 500 PPR encoder |
| **Emergency Stop** | Push-button with NO/NC contacts | 1 | System safety shutdown |
| **Limit Switches** | [igus® proximity switch](https://www.igus.eu/product/drylin_E_ini_kits_plastic_housing) | 4 | Position boundary detection |
| **48V Power Supply** | [MEAN WELL SDR-960-48](https://www.meanwell.com/webapp/product/search.aspx?prod=SDR-960) | 3 | Brushles motors power |
| **24V Power Supply** | [MEAN WELL SDR-240-24](https://www.meanwell.com/webapp/product/search.aspx?prod=SDR-240) | 1 | Stepper motor power |
| **24V Power Supply** | Generic power supply | 1 | igus® Drive D1 logic and MESA 7I77 field power |
| **5V Power Supply** | [MEAN WELL MDR-20-5](https://www.meanwell.com/webapp/product/search.aspx?prod=MDR-20)   | 1 | MESA 7I77 field I/O logic power |

## System Architecture

![Prototype System](assets/system_diagram.svg)

## Repository Structure

```txt
gantry-robot/
├── README.md                    # This file
├── assets/                      # Pictures and videos
├── docs/                        # Technical documentation
├── linuxcnc/                    # LinuxCNC configuration files
│   ├── configs/                 # Machine configurations
│   └── components/              # Custom LinuxCNC components
├── calibration/                 # Calibration code and measurements
│   ├── src/                     # Python analysis and calibration tools
│   └── measurements/            # Gantry robot and OptiTrack measurements
└── electrical_installation/     # Electrical documentation
    ├── schematics/              # KiCAD electrical diagrams
    └── photos/                  # Electrical installation photos
```

## License

This project contains multiple components with different licenses.

### General License (unless otherwise specified)

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">
<img alt="Creative Commons License badge" src="https://licensebuttons.net/l/by-sa/4.0/88x31.png"/>
</a>

[LinuxCNC Gantry Robot System](https://github.com/GTEC-UDC/linuxcnc_gantry_robot) © 2025 by [Tomás Domínguez Bolaño](https://orcid.org/0000-0001-7470-0315), [Valentín Barral Vales](https://orcid.org/0000-0001-8750-7960), [Carlos José Escudero Cascón](https://orcid.org/0000-0002-3877-1332), and [José Antonio García Naya](https://orcid.org/0000-0002-1944-4678) (CITIC Research Center, University of A Coruña, Spain) is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0). To view a copy of this license, see the [LICENSE](LICENSE) file or visit <https://creativecommons.org/licenses/by-sa/4.0/>.

### Documentation License ([docs/](docs/))

Copyright © 2000-2022 LinuxCNC.org\
Copyright © 2025 Tomás Domínguez Bolaño, Valentín Barral Vales, Carlos José Escudero Cascón, and José Antonio García Naya.

Permission is granted to copy, distribute and/or modify this document
under the terms of the GNU Free Documentation License, Version 1.3
or any later version published by the Free Software Foundation;
with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.
A copy of the license is included in the section entitled "GNU Free Documentation License".

### Software Licenses

- **LinuxCNC Components** (`linuxcnc/components/`): [GPL v2 or later](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
- **Calibration Source Code** (`calibration/src/`): [MIT License](https://opensource.org/licenses/MIT)

## Acknowledgments

This work has been supported by grant PID2022-137099NB-C42 (MADDIE) and by project TED2021-130240B-I00 (IVRY) funded by MCIN/AEI/10.13039/501100011033 and the European Union NextGenerationEU/PRTR.

<div align="center">
  <img alt="Acknowledgements logos" src="assets/ack_logos.svg" width="600"/>
</div>
