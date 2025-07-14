# Controladores Igus dryve D1

:::{admonition} Nota importante
:class: warning

**Esta sección requiere revisión**: La documentación de esta sección está basada en testbed de LinuxCNC y necesita ser actualizada para reflejar la configuración específica del robot pórtico de alta precisión, incluyendo los 4 controladores igus® dryve D1 utilizados (3 para motores sin escobillas NEMA 34 y 1 para motor paso a paso NEMA 24).
:::

:::{toctree}
:maxdepth: 2
:caption: Índice

01_pagina_start.md
02_pagina_motor.md
03_pagina_axis.md
04_pagina_communication.md
05_pagina_inputs_ouputs.md
06_pagina_drive_profile.md
07_pagina_oscilloscope.md
:::

En esta sección, describiremos en detalle la configuración de los
controladores Igus dryve D1. Para configurar los controladores es
necesario conectarlos mediante Ethernet a un PC. Si no sabemos la
dirección IP de un controlador podemos obtenerla al encenderlo o
reconectar el cable Ethernet, en estos casos el controlador mostrará su
dirección IP dígito a dígito en el visualizador de siete segmentos de su
frontal.

Una vez conectados los controladores, abriremos un navegador web y
pondremos la dirección IP del controlador que queramos configurar, esto
nos permitirá acceder a la interfaz web de configuración del
controlador. En las siguientes secciones se describen los parámetros de
configuración del controlador y los valores a aplicar en cada parámetro
para el motor sin escobillas y el motor paso a paso. Para una
información más detallada se recomienda consultar el manual de los
controladores (ver archivo
"`Operating Manual dryve D1 EN V3.0.1.pdf`").
