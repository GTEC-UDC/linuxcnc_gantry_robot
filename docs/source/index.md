# {{project}}

A large high-precision 3-axis gantry robot system using [LinuxCNC](https://www.linuxcnc.org), integrated with [Mesa Electronics](https://store.mesanet.com/) interface cards and [igus® dryve D1](https://www.igus.eu/product/D1) motor controllers.

The system was developed from our [LinuxCNC motor control testbed](https://github.com/your-org/linuxcnc-testbed), which ensured the main components of the system were able to work reliably.

The system includes a custom calibration solution that leverages an existing [OptiTrack](https://optitrack.com/) motion capture system in the installation room to measure and compensate for errors in the gantry movement. Using this solution the gantry robot can achieve sub-centimeter precision across the entire work envelope.

---

Copyright (C) 2000-2022 LinuxCNC.org\
Copyright (C) 2025 Tomás Domínguez Bolaño, Valentín Barral Vales, Carlos José Escudero Cascón, and José Antonio García Naya.

Permission is granted to copy, distribute and/or modify this document
under the terms of the GNU Free Documentation License, Version 1.3
or any later version published by the Free Software Foundation;
with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.
A copy of the license is included in the section entitled "GNU Free Documentation License".

---

This work has been supported by grant PID2022-137099NB-C42 (MADDIE) and by project TED2021-130240B-I00 (IVRY) funded by MCIN/AEI/10.13039/501100011033 and the European Union NextGenerationEU/PRTR.

:::{ext-image} images/logos/ack_logos.*
:width-html: 700px
:name: fig:ack_logos
:::

---

:::{note}
This documentation is currently under development and available only in Spanish. English translation is planned for future releases.
:::

:::{toctree}
:maxdepth: 2
:numbered:
:caption: Índice

doc/01_introduccion/introduccion.md
doc/02_igus_dryve_d1/00_index.md
doc/03_linuxcnc/00_index.md
:::

:::{toctree}
:maxdepth: 1

bibliografia.md
fdl-1.3.md
:::
