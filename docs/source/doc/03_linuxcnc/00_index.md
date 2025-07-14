(sec:linuxcnc)=
# LinuxCNC

:::{admonition} Nota importante
:class: warning

**Esta sección requiere revisión**: La documentación de esta sección está basada en el testbed de LinuxCNC y necesita ser actualizada para reflejar la configuración específica del robot pórtico, incluyendo la configuración de 3 ejes lineales (X, Y, Z), las tarjetas MESA 7I96S y 7I77, y la integración con el módulo de cinemática personalizado `calibxyzkins` para la compensación de errores de posicionamiento.
:::

:::{toctree}
:maxdepth: 2
:caption: Índice

01_instalacion.md
02_analisis_latencia.md
03_ajuste_latencia.md
04_configuracion_mesa_7i96s.md
05_configuracion_mesa_7i77.md
06_linuxcnc_introduccion.md
07_linuxcnc_uso_basico.md
08_linuxcnc_configuracion.md
:::

LinuxCNC (<https://linuxcnc.org/>), anteriormente conocido como el EMC, es un software Linux libre
y de código abierto que proporciona un sistema de control numérico para
controlar máquinas de CNC con ordenadores de propósito general.

En esta sección se proporciona una pequeña guía de uso y configuración
de LinuxCNC para el sistema del montaje de prueba. Para más detalles se recomienda consultar el
manual de usuario de LinuxCNC {cite}`linuxcncdoc`. Otros recursos de interés de LinuxCNC son también:

- Foro de LinuxCNC: <https://forum.linuxcnc.org/>.
- Vídeos "LinuxCNC for the Hobbyist" de "Joe Hildreth" en YouTube:
    <https://www.youtube.com/playlist?list=PLaamliiI72ntlrHKIFjh2VjmehRGgZpjm>
- Vídeos de "The Feral Engineer" en YouTube:
  - LinuxCNC bare bones:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpflFA3C8ZJ5H30vnReQXRii>
  - LinuxCNC Basic HAL tutorials:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpfpy3xu1bx3kndiktXZVwyg>
  - Classicladder tutorials:
        <https://www.youtube.com/playlist?list=PLTYvfbjLClpfAfJSGhZUecgXFwVPY5e09>
- Vídeo "CNC Motion Control with LinuxCNC + Mesa FPGA Card" de
    "Marco Reps" en YouTube:
    <https://www.youtube.com/watch?v=1dy8Dgzcgq4>
