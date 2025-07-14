# {{project}}

A large high-precision 3-axis gantry robot system using [LinuxCNC](https://www.linuxcnc.org), integrated with [Mesa Electronics](https://store.mesanet.com/) interface cards and [igus® dryve D1](https://www.igus.eu/product/D1) motor controllers.

The system was developed from our [LinuxCNC motor control testbed](https://github.com/your-org/linuxcnc-testbed), which ensured the main components of the system were able to work reliably.

The system includes a custom calibration solution that leverages an existing [OptiTrack](https://optitrack.com/) motion capture system in the installation room to measure and compensate for errors in the gantry movement. Using this solution the gantry robot can achieve sub-centimeter precision across the entire work envelope.

---

[LinuxCNC Gantry Robot System](https://github.com/GTEC-UDC/linuxcnc_testbed) © 2025 by [Tomás Domínguez Bolaño](https://orcid.org/0000-0001-7470-0315), [Valentín Barral Vales](https://orcid.org/0000-0001-8750-7960), [Carlos José Escudero Cascón](https://orcid.org/0000-0002-3877-1332), and [José Antonio García Naya](https://orcid.org/0000-0002-1944-4678) (CITIC Research Center, University of A Coruña, Spain) is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0). To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>.

This work has been supported by project TED2021-130240B-I00 (IVRY) funded by MCIN/AEI/10.13039/501100011033 and the European Union NextGenerationEU/PRTR.

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
bibliografia.md
:::
