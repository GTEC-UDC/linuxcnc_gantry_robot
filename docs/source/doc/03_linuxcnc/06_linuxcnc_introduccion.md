# Introducción a LinuxCNC

LinuxCNC es un conjunto de aplicaciones altamente personalizables para
el control máquinas de CNC, impresoras 3D, robots, y otros dispositivos
automatizados. Es capaz de proporcionar control coordinado de hasta 9
ejes de movimiento. LinuxCNC consta de varios componentes clave que
están integrados para formar un sistema completo
{cite}`linuxcncdoc`:

- Una GUI, que constituye la interfaz básica entre el operador, el
    software, y la máquina CNC en sí misma.
- La HAL, que permite enlazar las señales del mundo exterior con
    LinuxCNC y viceversa.
- Los módulos de alto nivel que coordinan la generación, ejecución, y
    control de movimiento de la máquina CNC, a saber, el controlador de
    movimiento, el controlador de entrada/salida, y el ejecutor de
    tareas.

En este documento se proporciona solo una pequeña guía de LinuxCNC, para
más detalles se recomienda consultar el manual de usuario de LinuxCNC
{cite}`linuxcncdoc`, en donde se detalla
ampliamente como usar el software. En un sistema con LinuxCNC instalado,
el manual se puede consultar haciendo clic en .

## Ejecutar LinuxCNC

Podemos ejecutar LinuxCNC haciendo clic en
{menuselection}`Applications menu --> CNC --> LinuxCNC` o mediante el comando `linuxcnc`, cuya forma de
uso se muestra en el {numref}`lst:linuxcnc_help`.

:::{code-block} text
:name: lst:linuxcnc_help
:caption: Uso del comando linuxcnc

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

Si hacemos clic en
{menuselection}`Applications menu --> CNC --> LinuxCNC` o ejecutamos el comando `linuxcnc` sin pasarle
como parámetro un archivo de configuración se abrirá el selector de
configuración de LinuxCNC, como se muestra en la
{numref}`fig:linuxcnc_conf_selector`.

:::{figure} images/linuxcnc/configuration_selector.png
:name: fig:linuxcnc_conf_selector

Selector de configuración de LinuxCNC.
:::

En el selector de configuración se muestran las configuraciones
disponibles en una estructura de árbol, reflejando la estructura de
directorios donde se almacenan, con dos nodos iniciales:

- **My configurations**: configuraciones del usuario, almacenadas en
    la carpeta .
- **Sample configurations**: configuraciones de ejemplo proporcionadas
    de serie con LinuxCNC. Estas se almacenan en .

Al hacer clic en una de las configuraciones se mostrará su información
en el recuadro derecho de la aplicación. Para arrancar LinuxCNC con una
configuración simplemente hay que hacer doble clic en ella o
seleccionarla y pulsar el botón {guilabel}`OK`.
Si marcamos la casilla "Create Desktop Shortcut", se creará además un
icono en el escritorio para lanzar directamente LinuxCNC con la
respectiva configuración. Por último, si la configuración es una de las
*Sample configurations*, LinuxCNC preguntará al usuario si copiarla a la
carpeta `~/linuxcnc/configs`, de forma que el usuario pueda modificarla
posteriormente. En caso de responder afirmativamente, posteriormente la
configuración aparecerá dentro de la categoría *My configurations*.

(sec:linuxcnc_intro_config)=
## Archivos de configuración

Una configuración de LinuxCNC se compone de varios archivos. Por
ejemplo, considerando una carpeta de configuración con nombre "robot",
para una configuración típica tendríamos los siguientes archivos:

- `robot.ini`: Configuración principal de LinuxCNC. Aquí se definen
    parámetros como velocidades, aceleraciones, configuración de ejes, y
    otros ajustes importantes.
- `robot.hal`: Archivo principal de la HAL. Contiene la configuración
    de la asignación de señales de LinuxCNC con la interfaz de hardware
    del sistema. Define cómo los componentes físicos se relacionan con
    las señales lógicas dentro de LinuxCNC. Al iniciar LinuxCNC, este
    archivo se lee y se procesa antes de que se cargue la GUI.
- `robot_custom.hal` (opcional): LinuxCNC permite especificar varios
    archivos `.hal`. Este archivo contendrá configuraciones adicionales
    de la HAL.
- `robot_postgui.hal` (opcional): Configuraciones de la HAL que se
    realizarán después de que la GUI se haya cargado. Esto puede incluir
    configuraciones de visualización como por ejemplo enlazar una señal
    de LinuxCNC con un elemento de la GUI para mostrar su valor.
- `rs274ngc.var` (opcional): Parámetros para el intérprete de G-code
    (ver {numref}`sec:linuxcnc_intro_gcode`)
    que serán persistentes entre distintas ejecuciones de LinuxCNC.
- `tool.tbl` (opcional): Configuración de la tabla de herramientas. Se
    utiliza para definir herramientas y sus propiedades, como
    dimensiones y compensaciones. Es importante para el sistema saber
    exactamente cómo está configurada cada herramienta para realizar
    operaciones precisas en las piezas de trabajo.

En la {numref}`sec:linuxcnc_configuration` se
muestra un ejemplo de configuración de LinuxCNC.

(sec:linuxcnc_intro_gcode)=
## Lenguaje G-code

El G-code es el lenguaje de programación más usado en CNC. Un programa
G-code consiste en una serie de instrucciones que indica a la máquina
cómo moverse o cómo realizar operaciones específicas. El G-code tiene
sus raíces en los primeros días de la automatización industrial. Se
desarrolló como una forma estándar de comunicar instrucciones a las
máquinas CNC en los años 50 y 60. Se estandarizó como RS-274 por la EIA
en 1963, y su revisión final se estandarizó como RS-274-D en 1979 y como
ISO 6984 en 1982. Posteriormente, surgieron numerosas implementaciones y
estándares derivados, desarrollados tanto por organismos públicos como
privados.

En LinuxCNC, el G-code es el lenguaje que se utiliza para controlar el
movimiento de la máquina. En particular, la versión implementada por
LinuxCNC se basa en el lenguaje RS274/NGC desarrollado por el NIST
{cite}`RS274NGC`. En la documentación de
LinuxCNC se documenta ampliamente el lenguaje G-code
{cite}`linuxcncdoc{sección G-code Programming}`. Como ejemplo, a continuación se presentan algunos comandos
de G-code.

- `G0 X10 Y5 Z3`: Movimiento rápido a las coordenadas X=10, Y=5, y
    Z=3.
- `F100`: Establece el *feed rate* (velocidad de movimiento) a 100
    unidades por minuto.
- `G1 X20 Y15`: Movimiento a las coordenadas X=20 e Y=15 a la
    velocidad establecida en el *feed rate*.
- `G1 F100 X20 Y15`: Establece el *feed rate* a 100 unidades por
    minuto y realiza un movimiento a las coordenadas X=20 e Y=15.
- `G2 X30 Y10 I5 J0`: Movimiento circular en sentido horario con
    centro en X=5, Y=0 y radio de 5 unidades.
- `G3 X40 Y5 I2 J3`: Movimiento circular en sentido antihorario con
    centro en X=2, Y=3 y radio de 5 unidades.
- `M3 S1000`: Encender el husillo a 1000 rpm en sentido horario.
- `M5`: Apagar el husillo.

Estos son solo algunos ejemplos básicos de comandos G-code. En la
práctica, los programas G-code se compondrán de varias líneas, cada una
con un comando, y como cualquier otro lenguaje de programación podrán
definir variables, subrutinas, y usar bucles o control de flujo.

(sec:linuxcnc_modes_of_operation)=
## Modos de operación

En LinuxCNC hay tres modos de operación, cada uno diseñado para un
propósito específico: manual, automático, y MDI. Estos modos definen
cómo se ingresan y ejecutan los comandos, y cada uno tiene sus propias
características distintivas:

- En el modo manual, los comandos se ingresan individualmente. Estos
    comandos son acciones directas, como "activar refrigerante" o
    "mover el eje X a 25 pulgadas por minuto". En las de interfaces
    gráficas se maneja normalmente mediante botones o atajos de teclado.
- El modo automático permite la ejecución completa de programas G-code
    almacenados en archivos. Un único comando puede cargar y ejecutar un
    archivo entero.
- El modo MDI permite ejecutar comandos individuales de G-code.

Es importante tener en cuenta que ciertos comandos, como *Abort*,
*Emergency Stop*, y *Feed Rate Override*, pueden usarse en todos los
modos.

## Interfaz gráfica

LinuxCNC proporciona diversas interfaces gráficas para controlar las
máquinas CNC. La interfaz específica a usar se configura en el archivo
`.ini`. La lista completa de interfaces gráficas disponibles con
imágenes y ejemplos se puede consultar en el manual de usuario de
LinuxCNC {cite}`linuxcncdoc`.

Una de las interfaces gráficas más populares es "AXIS", pensada para
ser controlada mediante teclado y ratón. Esta interfaz gráfica se
muestra en la {numref}`fig:linuxcnc_gui_axis_estop`. Por otra parte, LinuxCNC también dispone de la interfaz
"HALUI", una interfaz puramente hardware, que permite controlar la
máquina CNC solamente usando botones e interruptores físicos.

:::{figure} images/linuxcnc/linuxcnc_gui_axis.png
:name: fig:linuxcnc_gui_axis_estop

Interfaz gráfica "AXIS" de LinuxCNC.
:::

En el montaje de prueba hemos considerado la interfaz gráfica AXIS. La
ventana de esta interfaz, como se muestra en la
{numref}`fig:linuxcnc_gui_axis_estop`, contiene
los siguientes elementos:

- Un área de visualización con dos pestañas:

  - Pestaña "Preview": muestra la posición del punto controlado
        por la máquina. Posteriormente, mostrará la ruta trazada por la
        máquina.
  - Pestaña "DRO" (DRO): muestra la posición actual y todas las
        compensaciones.

- Una barra de menú y una barra de herramientas que permiten realizar
    diversas acciones.

- Pestaña "Manual Control": permite mover la máquina.

- Pestaña "MDI" (MDI): permite introducir programas de G-code
    manualmente, línea a línea.

- "Feed Override": permite escalar la velocidad de los movimientos
    programados.

- "Rapid Override": permite escalar la velocidad de los movimientos
    rápidos (e.g., códigos `G0` de G-code).

- "Jog Speed": permite configurar la velocidad de "jog", i.e., la
    velocidad cuando se controla el robot con los controles
    {guilabel}`+` y {guilabel}`-` de la pestaña "Manual Control".

- "Max Velocity": permite limitar la velocidad máxima de todos los
    movimientos programados.

- "Active G-codes": muestra los códigos G modales que están
    vigentes. Algunos de los más relevantes de los que se muestran en la
    {numref}`fig:linuxcnc_gui_axis_estop` son:

  - `G17`: Establece el plano de trabajo de la máquina en XY.
  - `G21`: Establece las unidades de medida en milímetros.
  - `G90`: Establece la modalidad de coordenadas absolutas.
  - `G94`: Establece que el "feed rate" (velocidad de avance) se
        interpretará en unidades por minuto.
  - `F0`: Establece el "feed rate" (velocidad de avance) en cero.

    La información detallada de los códigos G se puede consultar en el
    manual de usuario de LinuxCNC
    {cite}`linuxcncdoc{sección G-Codes}`,
    también disponible en
    <https://linuxcnc.org/docs/html/gcode/g-code.html>.

- Un área de visualización de texto que muestra el archivo de G-code
    cargado.

- Una barra de estado que muestra distintos datos de utilidad:

  - El estado de la máquina: "ESTOP" (parada de emergencia),
        "OFF" (apagada), o "ON" (encendida).
  - La herramienta insertada.
  - La posición mostrada: "relative" (mostrando todas las
        compensaciones), o "actual" (mostrando la posición de
        retroalimentación).
