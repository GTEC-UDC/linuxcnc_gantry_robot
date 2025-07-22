(sec:linuxcnc)=
# LinuxCNC

:::{note}
This section was taken from our LinuxCNC testbed project (<https://github.com/GTEC-UDC/linuxcnc_testbed>). It needs to be updated to reflect the gantry robot configuration.
:::

LinuxCNC (<https://linuxcnc.org/>), formerly known as the {{EMC}}, is a free and open-source Linux numerical control system for operating {{CNC}} machines using general-purpose computers.

This section provides a brief guide to using and configuring LinuxCNC for the testbed system. For more in-depth information, consult the LinuxCNC user manual {cite}`linuxcncdoc`. Other valuable LinuxCNC resources are:

- LinuxCNC Forum: <https://forum.linuxcnc.org/>
- "LinuxCNC for the Hobbyist" video series by "Joe Hildreth" on YouTube:
    <https://www.youtube.com/playlist?list=PLaamliiI72ntlrHKIFjh2VjmehRGgZpjm>
- Videos by "The Feral Engineer" on YouTube:
  - LinuxCNC bare bones:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpflFA3C8ZJ5H30vnReQXRii>
  - LinuxCNC Basic {{HAL}} tutorials:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpfpy3xu1bx3kndiktXZVwyg>
  - Classicladder tutorials:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpfAfJSGhZUecgXFwVPY5e09>
- "CNC Motion Control with LinuxCNC + Mesa FPGA Card" video by "Marco Reps" on YouTube:
    <https://www.youtube.com/watch?v=1dy8Dgzcgq4>

:::{toctree}
:maxdepth: 2
:caption: Table of Contents

01_installation.md
02_latency_analysis.md
03_latency_tuning.md
04_mesa_7i96s_configuration.md
05_mesa_7i77_configuration.md
06_linuxcnc_introduction.md
07_linuxcnc_basic_usage.md
08_linuxcnc_configuration.md
:::
