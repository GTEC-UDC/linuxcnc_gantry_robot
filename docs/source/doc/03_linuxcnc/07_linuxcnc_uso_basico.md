---
myst:
  substitutions:
    button_estop: "![button_estop](images/linuxcnc/linuxcnc_gui_axis_button_estop.png){height=\"16px\"}"
    button_on_disabled: "![button_on_disabled](images/linuxcnc/linuxcnc_gui_axis_button_on_disabled.png){height=\"16px\"}"
    button_on: "![button_on](images/linuxcnc/linuxcnc_gui_axis_button_on.png){height=\"16px\"}"
    button_run: "![button_run](images/linuxcnc/linuxcnc_gui_axis_button_run.png){height=\"16px\"}"
    homed_symbol: "![homed_symbol](images/linuxcnc/linuxcnc_gui_axis_homed_symbol.png){height=\"16px\"}"
---

(sec:linuxcnc_usage)=
# Uso básico de LinuxCNC

Durante el desarrollo del montaje de prueba se han elaborado tres
configuraciones principales de LinuxCNC:

- `mesa_7i96s_7i77_xy`: Simula un robot con ejes X e Y, donde el motor
    sin escobillas controla el eje X, y el motor paso a paso el eje Y.
- `mesa_7i96s_7i77_xx`: Simula un robot con un único eje X, donde
    ambos motores, sin escobillas y paso a paso, controlan al mismo
    tiempo el eje. Por lo tanto, en este caso ambos motores se mueven
    síncronamente a la misma velocidad.
- `mesa_7i96s_7i77_xc`: Simula un robot con un eje X y un eje C,
    siendo el eje C el de rotación alrededor del eje Z. El motor sin
    escobillas controla el eje X, y el motor paso a paso el eje C.

En las siguientes secciones se explica como usar LinuxCNC con estas
configuraciones.

(sec:linuxcnc_usage_gui_axis)=
## Control mediante la interfaz gráfica AXIS

Al arrancar LinuxCNC con una de las configuraciones anteriores se abrirá
la interfaz gráfica AXIS como se muestra en la
{numref}`fig:linuxcnc_gui_axis_estop`. A
continuación se explica el proceso para controlar la máquina con esta
interfaz.

### Establecer el estado de LinuxCNC a "ON"

El estado inicial de LinuxCNC será "ESTOP" (parada de emergencia),
como se indica en la parte inferior izquierda de la ventana, y por lo
tanto el movimiento del robot estará deshabilitado. Para poder arrancar
el robot en primer lugar deberemos eliminar la condición de "ESTOP".
para esto hacemos lo siguiente:

1. Desactivar el interruptor físico de parada de emergencia (ver
    {numref}`fig:gantry_installation`). Si este
    interruptor está activado se fuerza el estado de parada de
    emergencia en LinuxCNC.
2. Desactivar el estado de parada de emergencia en LinuxCNC pulsando el
    botón {{button_estop}}.

Una vez desactivado el estado de parada de emergencia, LinuxCNC pasará
al estado "OFF" (apagado) y el botón de arranque pasará de
desactivado: {{button_on_disabled}} a activado: {{button_on}}.
Para empezar a usar el robot pulsaremos este botón, de esta forma
LinuxCNC pasará al estado "ON" (encendido). En la
{numref}`fig:linuxcnc_gui_axis_on` se muestra
la interfaz AXIS en el estado "ON".

:::{figure} images/linuxcnc/linuxcnc_gui_axis_on.png
:name: fig:linuxcnc_gui_axis_on

Interfaz gráfica "AXIS" de LinuxCNC en estado "ON".
:::

### Referenciar la máquina

Una vez que LinuxCNC está en estado "ON", podemos controlar
manualmente la máquina a través de los controles {guilabel}`-` y {guilabel}`+` de la pestaña
"Manual Control". Sin embargo, para ejecutar comandos específicos de
posicionamiento de G-code, e.g., mover la máquina a (X=1, Y=5), es
necesario llevar a cabo el proceso de "homing" o referenciación de la
máquina. El procedimiento de "homing" implica establecer un punto de
referencia preciso para todos los ejes de la máquina, de forma que
LinuxCNC tenga conocimiento exacto de la posición de la máquina.

Para realizar el proceso de "homing" podemos hacer clic en el botón
{guilabel}`Home All` de la pestaña "Manual
Control" o en la entrada de menú
{menuselection}`Machine --> Homing --> Home all axes`. En las configuraciones de prueba el proceso de
"homing" involucra el uso de los interruptores de límite. El proceso
que sigue LinuxCNC para realizar el "homing" mediante interruptores de
límite es el siguiente:

1. Mover el motor hacia el interruptor de límite hasta encontrarlo,
    i.e., activarlo.
2. Mover el motor en sentido opuesto hasta desactivar el interruptor de
    límite.
3. Mover el motor otra vez hacia el interruptor de límite hasta
    encontrarlo, esta vez a una velocidad inferior para localizar la
    posición del interruptor de forma precisa.
4. Mover el motor hasta la posición de referencia "home".

En las configuraciones `mesa_7i96s_7i77_xy` y `mesa_7i96s_7i77_xx`
deberemos activar manualmente los interruptores de límite para ambos
motores. En la configuración `mesa_7i96s_7i77_xc` solo deberemos activar
manualmente el interruptor de límite para el motor sin escobillas, el
motor paso a paso en este caso usa un proceso de "homing" distinto que
simplemente busca la posición del pulso de índice del encoder.

En la {numref}`fig:linuxcnc_gui_axis_on_homed`
se muestra la ventana de la interfaz después de completar el proceso de
referenciado. Ahora se puede ver el símbolo {{homed_symbol}}
al lado de la información de los ejes X e Y en el área de visualización,
lo que indica que los ejes están referenciados.

:::{figure} images/linuxcnc/linuxcnc_gui_axis_on_homed.png
:name: fig:linuxcnc_gui_axis_on_homed

Interfaz gráfica "AXIS" de LinuxCNC en estado "ON" y con todos los ejes referenciados.
:::

### Controlar la máquina

Como se comentó en la
{numref}`sec:linuxcnc_modes_of_operation`,
LinuxCNC dispone de 3 modos de control: manual, MDI, y automático. La
interfaz AXIS permite controlar la máquina con estos modos de la
siguiente forma:

- **Modo manual**: podemos controlar la máquina en modo manual a
    través de los controles {guilabel}`-` y
    {guilabel}`+` de la pestaña "Manual
    Control".
- **Modo MDI**: podemos usar el modo MDI a través de la pestaña
    "MDI", donde se pueden introducir comandos G-code línea a línea.
- **Modo automático**: podemos cargar un programa de G-code en archivo
    haciendo clic en {menuselection}`File --> Open` y a continuación ejecutarlo en modo automático haciendo clic en el botón {{button_run}}
    o pulsando la tecla {kbd}`R`.

Para más información acerca del control mediante G-code consultar la
sección "G-code programming" en el manual de LinuxCNC
{cite}`linuxcncdoc`.

## Control programado

Podemos controlar LinuxCNC mediante programas que incluyan una secuencia
de instrucciones de las siguientes dos formas:

1. Usando programas de G-code en archivo como se comentó en la sección
    anterior.
2. Usando programas en Python utilizando la biblioteca `linuxcnc`,
    incluida con LinuxCNC, que permite interactuar con el proceso en
    ejecución de LinuxCNC. Para más información consultar la sección
    "Python Interface" en el manual de usuario de LinuxCNC. En el
    {numref}`lst:linuxcnc_python` se muestra un
    ejemplo de control del robot con Python mediante el envío de
    comandos G-code en modo MDI.

:::{code-block} python
:name: lst:linuxcnc_python
:caption: Ejemplo de uso de Python para interactuar con LinuxCNC

#!/usr/bin/env python3
# Example of LinuxCNC control with Python
# See the LinucCNC user manual, section 13.5 - Python Interface

import sys
import linuxcnc


def control_robot(c: linuxcnc.command) -> None:
    def set_feed_rate(v: float):
        # set robot feed rate
        c.mdi(f"F{v}")
        c.wait_complete()

    def go_to(x: float, y: float):
        # go to position (x, y)
        print(f"Going to ({x}, {y})...", end="", flush=True)
        c.mdi(f"G1 X{x} Y{y}")
        while (ret := c.wait_complete(1)) == -1:
            continue
        print(" done")
        if ret == linuxcnc.RCS_ERROR:
            print("RCS_ERROR")

    # Put your robot commands here
    set_feed_rate(400)
    go_to(0, 0)


def main():
    s = linuxcnc.stat()  # connect to the status channel
    c = linuxcnc.command()  # connect to the command channel

    def ok_for_mdi() -> bool:
        s.poll()
        return (
            not s.estop
            and s.enabled
            and (s.homed.count(1) == s.joints)
            and (s.interp_state == linuxcnc.INTERP_IDLE)
        )

    if ok_for_mdi():
        c.mode(linuxcnc.MODE_MDI)
        c.wait_complete()  # wait until mode switch executed
        print("OK, running...")
        try:
            control_robot(c)
        except KeyboardInterrupt:
            c.abort()
            sys.exit(1)
    else:
        print("Not OK for running. Check that the robot is homed and idle.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except linuxcnc.error as e:
        print("error: ", e)
        print("is LinuxCNC running?")
        sys.exit(1)
:::
