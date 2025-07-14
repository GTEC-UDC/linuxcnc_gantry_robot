(sec:page_input_outputs)=
# Página "Inputs/Outputs" 

La página de configuración "Inputs/Outputs" se muestra en la
{numref}`fig:conf_stepper_5`. Esta página
permite configurar las entradas y salidas del controlador.

:::{figure} images/config-stepper/05-inputs_outputs.png
:name: fig:conf_stepper_5

Página de configuración de "Inputs/Outputs" del controlador del motor paso a paso.
:::

El nivel de la lógica digital usado por el controlador se establece
alimentando la entrada X2.11 con un voltaje entre 5 V y 24 V. La lógica
digital del controlador funciona de la siguiente forma:

- Las salidas digitales se establecen a 0 V para nivel bajo (L) y al
    voltaje de X2.11 para nivel alto (H).
- Las entradas digitales se evaluarán a nivel bajo (L) para voltajes
    de 0 % \-- 10 % del voltaje de X2.11, y se evaluarán a nivel
    alto (H) para valores mayores que 60 % del voltaje de X2.11.

Estos niveles se ilustran en la
{numref}`fig:controller_logic_levels`.

:::{figure} images/logic_levels/fig.*
:name: fig:controller_logic_levels

Niveles de la lógica digital usada por el controlador.
:::

Para interactuar con las entradas y salidas digitales del controlador
usamos las placas MESA 7I96S y 7I77:

- La placa MESA 7I96S se usa para enviar las señales de paso y
    dirección al controlador del motor paso a paso, estas señales
    emplean lógica de 5 V.
- La placa MESA 7I77 se usa para enviar las señales "start" y
    "enable", y leer las salidas "ready", "alert", y "error" de
    los controladores (ver esquema de conexionado en el archivo
    `pruebas_robot.pdf`). El voltaje de la lógica para la placa MESA
    7I77 se puede ajustar alimentando la entrada TB2.1 ("field power")
    con el voltaje deseado en un rango entre 5 V y 28 V.

Debido a que la placa MESA 7I96S solamente puede usar lógica de 5 V para
las señales de paso y dirección, hemos establecido el voltaje de la
lógica de los controladores Igus dryve D1 (entrada X2.11) y de la placa
MESA 7I77 (entrada TB2.1) a 5 V.

Las secciones disponibles en esta página son:

- **Digital Inputs**: Muestra las entradas digitales y permite
    seleccionar para cada una entre normalmente abierta (H) o
    normalmente cerrada (L). Las entradas normalmente abiertas (H) se
    activarán cuando se reciba una señal alta. Por el contrario, las
    entradas normalmente cerradas se activarán cuando se reciba una
    señal baja (L). Dejaremos todas establecidas al valor por defecto
    (H).

    :::{note}
    Las etiquetas de las entradas digitales mostradas en esta página
    variarán dependiendo del modo de control del motor seleccionado en
    la página "Drive Profile" (ver
    {numref}`sec:page_drive_profile`). En la
    {numref}`fig:conf_stepper_5` se muestra la
    configuración del motor paso a paso, que muestra las entradas para
    el modo de control "step/direction".
    :::

- **Digital Outputs**: Muestra las salidas digitales y permite
    seleccionar para cada una entre normalmente abierta (H) o
    normalmente cerrada (L). Dejaremos todas establecidas al valor por
    defecto (H).

- **Analog Inputs**: Muestra las entradas analógicas y permite
    establecer el rango de valores soportado de 0 V \-- 10 V o de -10 V
    \-- 10 V. En nuestro caso usaremos la entrada analógica AI 1 con
    señales de -10 V \-- 10 V para controlar la velocidad del motor sin
    escobillas, como se comentó en la
    {numref}`sec:axis_absolute_feedback`. Por
    lo tanto en el controlador del motor sin escobillas estableceremos
    la opción AI 1 al valor ± 10 VDC. La opción AI 2 la dejaremos sin
    modificar ya que no usaremos esa entrada.

- **Digital Input Switching**: Este parámetro determina cómo el
    sistema interpreta las señales de entrada digitales. Las opciones
    disponibles son PNP y NPN:

  - **PNP** (sourcing): En el estado activado, la entrada se eleva
        al voltaje aplicado en X2.11. En el estado no activado, la
        entrada se lleva a tierra a través de una resistencia de
        "pull-down". En este caso, la corriente fluye desde la salida
        del sistema de control de nivel superior hasta la entrada del
        Igus dryve D1.
  - **NPN** (sinking): En el estado activado, la entrada se lleva a
        tierra. En el estado no activado, la entrada se eleva al voltaje
        aplicado en X2.11 debido a una resistencia de "pull-up". En
        este caso, la corriente fluye desde la entrada del Igus dryve D1
        hasta la salida del sistema de control de nivel superior.

    En nuestro caso, todas las entradas y salidas de las placas MESA son
    de tipo PNP (sourcing), por lo que dejaremos establecida esta opción
    al valor por defecto "PNP".
