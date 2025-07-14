# Introducción

El robot grúa utiliza LinuxCNC como plataforma de control principal, integrado con tarjetas de interfaz Mesa Electronics y controladores de motor igus® dryve D1. El diagrama del sistema se muestra en la {numref}`fig:system_diagram`. Este sistema fue desarrollado a partir de nuestro [LinuxCNC testbed](https://github.com/your-org/linuxcnc-testbed).

:::{ext-figure} images/system_diagram/system_diagram.*
:height-html: 400px
:name: fig:system_diagram

Esquema del sistema del robot grúa.
:::

## LinuxCNC

LinuxCNC, previamente el {{EMC}}, es un sistema de software para el control
por ordenador de máquinas herramienta como fresadoras y tornos, robots
como puma y scara, y otras máquinas controladas por ordenador de hasta 9
ejes. LinuxCNC es software libre con código fuente abierto. Las
versiones actuales de LinuxCNC están totalmente licenciadas bajo la
[GPL](https://www.gnu.org/licenses/gpl.html) y la
[LGPL](https://gnu.org/licenses/lgpl.html).

En nuestro sistema usamos LinuxCNC para coordinar el control de 3 ejes lineales (X, Y, Z) del robot pórtico mediante las placas MESA 7I96S y 7I77, que se comunican con los controladores igus® dryve D1. LinuxCNC se encarga de coordinar el funcionamiento de todos los motores, proporcionándonos un control preciso y en tiempo real del sistema con un volumen de trabajo de 5.3m (X) × 5.2m (Y) × 1m (Z).

En la {numref}`sec:linuxcnc` se describe en
detalle el funcionamiento y la configuración de LinuxCNC.

## Hardware del sistema

En la {numref}`fig:gantry_installation` se muestra una
fotografía del robot grúa instalado. A continuación se describen los elementos principales de este sistema.

:::{figure} images/gantry_robot.*
:name: fig:gantry_installation

Estructura del robot grúa.
:::

### Componentes principales

- **Computadora de control**: PC ejecutando LinuxCNC para coordinación de motores en tiempo real

- **4 controladores de motores** [igus® dryve D1](https://www.igus.eu/product/D1): Los controladores igus® dryve D1 son dispositivos utilizados para controlar motores paso a paso, de corriente continua, y sin escobillas en aplicaciones industriales y de automatización. Los igus® dryve D1 admiten las siguientes formas de interacción con sistemas de control:

  - **CANopen**: Protocolo de comunicación usado en sistemas de automatización industrial, basado en el bus CAN (ISO 11898).
  - **Modbus TCP**: Protocolo de comunicación ampliamente utilizado en aplicaciones industriales para la transmisión de datos en redes Ethernet sobre el protocolo TCP.
  - **Señales analógicas y digitales**: Además de las opciones de comunicación en red, los dryve D1 pueden recibir señales analógicas y digitales para el control directo.

    En nuestro caso nos comunicamos con los controladores igus® dryve D1 mediante las placas MESA 7I96S y 7I77 usando señales digitales y analógicas. De esta forma, podemos emplear LinuxCNC para tener un control preciso y en tiempo real sobre el funcionamiento de los motores en el sistema.

### Tarjetas de interfaz

- **Tarjeta principal** [MESA 7I96S](http://store.mesanet.com/index.php?route=product/product&product_id=374): Es la interfaz de hardware principal entre LinuxCNC y los controladores igus® dryve D1. Esta placa está conectada a la computadora que ejecuta LinuxCNC a través de una conexión Ethernet. Sus funciones principales incluyen:

  - Controlar el motor paso a paso del eje Z enviando señales de paso y dirección al controlador igus® dryve D1 correspondiente.
  - Recibir las señales de los interruptores de límite inductivos.

- **Tarjeta de expansión** [MESA 7I77](http://store.mesanet.com/index.php?route=product/product&product_id=120): Está conectada a la placa 7I96S mediante un cable plano de 25 pines. Sus funciones principales incluyen:

  - Controlar los motores sin escobillas de los ejes X e Y enviando señales analógicas de velocidad a los controladores igus® dryve D1 correspondientes.
  - Recibir las señales de posición de los encoders de los motores.
  - Recibir las señales de advertencia y error provenientes de los controladores.
  - Recibir la señal de parada de emergencia al presionar el interruptor de parada de emergencia.

### Motores y actuadores

- **Motores del eje X**: 2x [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) - NEMA 34 sin escobillas con encoder de 1000 PPR

- **Motor del eje Y**: 1x [igus® MOT-EC-86-C-I-A](https://www.igus.eu/product/MOT-EC-86-C-I-A) - NEMA 34 sin escobillas con encoder de 1000 PPR

- **Motor del eje Z**: 1x [igus® MOT-AN-S-060-035-060-M-C-AAAC](https://www.igus.eu/product/motors-and-gears) - NEMA 24 paso a paso con encoder de 500 PPR

### Sistemas de seguridad y sensores

- **Interruptor de parada de emergencia**: Pulsador con contactos NO/NC para parada segura del sistema

- **Sensores de límite**: 4x sensores inductivos igus® para detección de límites de posición

- **Sistema de indicadores LED**: Sistema de desarrollo propio con LEDs rojo, amarillo y verde, que permite mostrar visualmente el estado del sistema.

### Alimentación eléctrica

- **Fuentes de 48V**: 3x MEAN WELL SDR-960 para alimentación de motores sin escobillas
- **Fuente de 24V**: 1x MEAN WELL SDR-240 para alimentación del motor paso a paso
- **Fuente de 24V adicional**: Para lógica de igus® dryve D1 y alimentación de campo MESA 7I77
- **Fuente de 5V**: MEAN WELL MDR-20-5 para lógica de E/S de campo MESA 7I77

### Unidades lineales

- **Construcción robusta**: Construido con unidades lineales igus® autolubricantes que permiten operación de por vida de las partes móviles sin lubricación externa

## Sistema de calibración

Este proyecto incluye los siguientes componentes de calibración:

- **Módulo de cinemática LinuxCNC personalizado `calibxyzkins`** en `linuxcnc/components/linuxcnc_calibrated_xyz_kins`: permite compensar los errores de posicionamiento en tiempo real
- **Software de análisis de calibración** en la carpeta `calibration/`: herramientas basadas en Python para procesar datos de OptiTrack y generar parámetros de calibración

Esta solución permite al robot grúa lograr precisión sub-centimétrica en todo el volumen de trabajo de 5.3m × 5.2m × 1m.
