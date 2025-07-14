(sec:page_axis)=
# Página "Axis"

La página de configuración "Axis" se muestra en la
{numref}`fig:conf_stepper_3`. Como se puede ver en la figura, los
parámetros usan las unidades establecidas en la página de
configuración inicial (ver {numref}`sec:conf_start`), así, los de
posición están en grados (°), los de velocidad en grados por segundo
(°/s), y los de aceleración en grados por segundo al cuadrado
(°/s^2^). A continuación se describen las distintas opciones
disponibles en esta página y como deben ser establecidas.

:::{figure} images/config-stepper/03-axis.png
:name: fig:conf_stepper_3

Página de configuración de "eje" del controlador del motor paso a paso.
:::

## Axis

Esta sección contiene los siguientes parámetros:

- **Available Stroke**: Establece la ventana de movimiento para el
    modo "ABS" (Absolute Positioning). No usaremos este modo, así que
    este parámetro es irrelevante para nosotros.
- **Feed Rate**: En ejes lineales este parámetro indica el
    desplazamiento del eje por rotación del motor. Nosotros consideramos
    un eje rotatorio y en este caso debemos establecer este parámetro a
    360° tal y como indica el manual del controlador en su Sección
    5.5.1.

(sec:axis_motion_limits)=
## Motion Limits

Esta sección contiene los siguientes parámetros:

- **Max. Velocity (°/s)**: Máxima velocidad del motor. Sirve como
    límite en los modos de programación de movimientos disponibles en la
    página "Drive Profile" (ver
    {numref}`sec:page_drive_profile`). En el
    caso del motor paso a paso la velocidad estará controlará mediante
    la señal de paso que recibirá el controlador, por lo que queremos
    que este parámetro sea lo mayor posible. En el caso del motor sin
    escobillas la velocidad máxima se establecerá en la página "Drive
    Profile", con un valor no superior al establecido en este
    parámetro. Por lo tanto estableceremos este parámetro a su valor
    máximo: 100000 °/s.

- **Jog Velocity (°/s)**: Velocidad del motor para el posicionamiento
    manual disponibles en la página "Drive Profile" (ver
    {numref}`sec:page_drive_profile`). Este
    parámetro solo es útil para realizar pruebas desde la interfaz web
    del controlador, en nuestro caso lo hemos establecido a 360 °/s.
    Para el sistema final este parámetro es irrelevante.

- **Max. Acceleration (°/s{sup}`2`)**: Aceleración máxima del motor. Es la
    aceleración usada en el posicionamiento manual disponible en la
    página "Drive Profile" (ver
    {numref}`sec:page_drive_profile`). También
    sirve como límite en los modos de programación de movimientos
    disponibles en la página "Drive Profile". Al igual que la
    velocidad, para el caso del motor paso a paso la aceleración estará
    controlará mediante la señal de paso que recibirá el controlador. En
    el caso del motor sin escobillas la aceleración máxima también se
    establecerá en la página "Drive Profile", con un valor no superior
    al establecido en este parámetro. Por lo tanto estableceremos este
    parámetro a su valor máximo: 1000000 °/s{sup}`2`.

- **S-Curve (%)**: Permite controlar la tasa de cambio de la
    aceleración, conocida como "jerk"
    {cite}`enwiki:1178778094`. Puede ajustarse
    entre 0 % y 100 % para controlar la suavidad de las transiciones de
    aceleración y desaceleración en el movimiento del motor. Valores más
    bajos producirán cambios bruscos en la aceleración, lo que genera
    niveles de "jerk" más altos y, en consecuencia, movimientos menos
    suaves que pueden causar vibraciones no deseadas y tensiones en el
    sistema. En contraste, valores más altos reducirán el "jerk", lo
    que resulta en transiciones de aceleración y desaceleración más
    suaves, minimizando las vibraciones y el desgaste en el motor y la
    maquinaria.

    Si deseamos que un controlador externo (como LinuxCNC) tenga un
    control total sobre el movimiento del motor estableceremos este
    parámetro a 0 %. En este caso, se desactiva cualquier suavizado de
    transiciones de aceleración y desaceleración dentro del propio
    controlador del motor, permitiendo que el controlador externo
    gestione directamente el movimiento.

    Sin embargo, el controlador de movimiento actual de LinuxCNC no
    dispone de limitación del "jerk", i.e., usa aceleración constante.
    Podría ser deseable establecer en este parámetro un valor mayor que
    0 % para limitar el "jerk" y evitar vibraciones no deseadas y
    tensiones en el sistema. Sin embargo, esto tendría la desventaja de
    aumentar el error de seguimiento dentro de LinuxCNC. Por lo tanto,
    en caso de querer establecer esta opción a un valor mayor que 0 %
    sería importante encontrar un equilibrio entre la suavidad del
    movimiento y la precisión del seguimiento.

    En nuestro caso hemos establecido el parámetro a 0 %.

- **Quick-Stop (°/s{sup}`2`)**: Desaceleración cuando se detiene un
    movimiento en caso de emergencia. Se ejecutará una parada rápida en
    el caso de que se revoque la señal de "Enable" (entrada digital
    X2.7) del controlador.

    :::{important}
    Es necesario asegurarse de que la desaceleración especificada sea
    adecuada para la aplicación prevista. Una desaceleración demasiado
    baja podría tardar demasiado tiempo en detener el movimiento del
    robot, por otra parte una desaceleración demasiado elevada podría
    dañar la estructura mecánica del robot.
    :::

    En el montaje de prueba hemos establecido este parámetro a 50000
    °/s{sup}`2`.

- **Following Error (°)**: Desviación admisible de la posición real
    con respecto a la posición deseada. Si se alcanza el 50 % del error
    de seguimiento permitido, se emite un aviso (warning). Si se supera
    el error de seguimiento permitido, el movimiento se detiene y se
    emite un error.

    En el montaje de prueba hemos establecido este parámetro a 20°.

- **Positioning Window (°)**: Ventana de posicionamiento. Se utiliza
    para definir un rango de posición alrededor de un punto de destino
    en una dirección positiva y negativa. Por ejemplo, si el objetivo es
    llegar a 100 mm y se establece una ventana de posicionamiento de 10
    mm, el sistema considerará que la posición está dentro del rango
    objetivo si se encuentra en cualquier lugar entre 90 mm y 110 mm. Si
    la posición real del motor se encuentra dentro de esta ventana, se
    considera que el movimiento ha finalizado, incluso si el motor está
    bloqueado mecánicamente. Esto se hace para evitar que el sistema
    continúe intentando alcanzar una posición exacta en caso de bloqueo.
    Si la ventana de posicionamiento se establece a 0, se desactiva esta
    función y el sistema no tomará en cuenta el rango alrededor del
    punto de destino.

    En el montaje de prueba hemos establecido este parámetro a 0, por lo
    tanto esta función está desactivada.

- **Positioning Time (ms)**: Tiempo de posicionamiento. Especifica
    cuánto tiempo debe mantenerse la posición real dentro del rango
    definido por la ventana de posicionamiento antes de que se considere
    que un movimiento ha finalizado. Este tiempo se establece en
    milisegundos y sirve como una medida de estabilidad y precisión en
    el posicionamiento.

    En el montaje de prueba hemos establecido este parámetro a 0.

(sec:limit_switch)=
## Limit Switch

Incluye un parámetro "Position" que permite especificar la posición y
el número de sensores de límites usados.

En el montaje de prueba los sensores de límites no se conectan a los
controladores, solo se conectan a la placa MESA 7I96S, de forma que los
límites son gestionados íntegramente por LinuxCNC. Por lo tanto
establecemos el parámetro "Position" a "None".

## Reference

Permite seleccionar el método de referencia ("homing") preferido y el
desplazamiento de posición ("offset").

Al igual que los límites de movimiento robot (ver
{numref}`sec:limit_switch`), el proceso de
"homing" también estará controlado íntegramente por LinuxCNC. Por lo
tanto hemos establecido los siguientes parámetros:

- **Method**: SCP (Set Current Position)
- **Offset (°)**: 0

(sec:axis_absolute_feedback)=
## Absolute Feedback

El controlador Igus Drive D1 dispone de dos entradas analógicas, AI 1
(Analog Input 1, entrada X4.1) y AI 2 (Analog Input 2, entrada X4.2),
que se utilizan para configurar y controlar la posición o velocidad
objetivo y la posición actual del sistema, respectivamente. En nuestro
sistema usaremos la entrada analógica AI 1 para controlar la velocidad
del motor sin escobillas, la entrada analógica AI 2 no sé usará. En el
caso del motor paso a paso no se usarán estas entradas, por lo tanto
esta sección solo es relevante para el motor sin escobillas. A
continuación se describen los para parámetros relativos a las entradas
analógicas disponibles en esta sección.

- **Parámetros relativos a AI 1 (entrada X4.1)**:

    La entrada AI 1 se usará para controlar la velocidad del motor sin
    escobillas (ver {numref}`sec:page_drive_profile`). El voltaje de control analógico de entrada será de
    ± 10 V, lo cual deberá configurarse en la página "Inputs/Outputs"
    (ver {numref}`sec:page_input_outputs`), y
    habrá que tenerlo en cuenta a la hora de establecer los parámetros
    relativos a AI 1 que se indican a continuación.

  - **AI 1 Target Value Min. (V)**: Valor de tensión mínimo en la
        entrada analógica AI 1. Establecemos su valor a -10 V.
  - **AI 1 Target Value Max. (V)**: Valor de tensión máximo en la
        entrada analógica AI 1. Establecemos su valor a 10 V.
  - **AI 1 Dead Band Zero Value (V)**: Permite establecer una banda
        muerta colocada simétricamente alrededor de 0 V en la señal
        objetivo correspondiente a la entrada analógica AI 1. Este
        parámetro se puede especificar en pasos de 0.001 V. Establecemos
        su valor a 0 V.
  - **AI 1 Dead Band Input Signal (V)**: Permite establecer una
        banda muerta colocada simétricamente alrededor de 0 V en la
        señal de entrada de la Entrada Analógica AI 1. Este parámetro se
        puede especificar en pasos de 0.001 V. Establecemos su valor a 0
        V.
  - **AI 1 Filter (ms)**: Intervalo para promediar la señal. Se
        utiliza para filtrar las variaciones bruscas de la señal y
        evitar inconsistencias en el movimiento. Valores bajos resultan
        en un sistema que responde rápidamente pero que es más
        susceptible al ruido o interferencias. Valores altos resultan en
        un sistema más estable pero con un mayor tiempo de respuesta.
        Establecemos su valor a 10 ms.

    Los parámetros de banda muerta, "AI 1 Dead Band Zero Value" y "AI
    1 Dead Band Input Signal", se pueden usar para minimizar
    movimientos no deseados del motor durante el estado de reposo
    causados por un mayor rizado de la señal de entrada u otras
    interferencias. Considerando los anteriores parámetros, si tenemos
    el voltaje analógico de entrada $x$ ya filtrado según lo
    especificado en el parámetro "AI 1 Filter", la posición o
    velocidad objetivo se calculará mediante las siguientes funciones de
    transferencia:

  - $f_{\text{ZV}}(\cdot)$, correspondiente al parámetro "AI 1 Dead
        Band Zero Value" y mostrada en la
        {numref}`fig:deadband_zv`.
  - $f_{\text{IS}}(\cdot)$, correspondiente al parámetro "AI 1 Dead
        Band Input Signal" y mostrada en la
        {numref}`fig:deadband_is`.

    de forma que para el valor analógico de entrada $x$ la posición o
    velocidad objetivo será:

    $$y = (f_{\text{ZV}} \circ f_{\text{IS}})(x) = f_{\text{ZV}}(f_{\text{IS}}(x))$$

    :::{note}
    El cálculo de la posición o velocidad objetivo no está especificado
    en el manual del controlador (considerando la versión del manual
    3.0.1, la más reciente a fecha de este documento) y se ha obtenido
    experimentalmente. El manual solo describe los parámetros "AI 1
    Dead Band Zero Value" y "AI 1 Dead Band Input Signal" de manera
    textual, de forma similar a como se han descrito más arriba.
    :::

:::{figure} images/f_is/fig.*
:name: fig:deadband_zv

Función de transferencia $f_{\text{ZV}}(\cdot)$.
:::

:::{figure} images/f_is/fig.*
:name: fig:deadband_is

Función de transferencia $f_{\text{IS}}(\cdot)$.
:::

- **Parámetros relativos a AI 2 (entrada X4.2)**:

    La entrada analógica AI 2 sirve para proporcionar información de
    posición al controlador mediante una señal analógica. En nuestro
    caso no usaremos esta entrada, por lo que los parámetros relativos
    esta entrada son irrelevantes para nosotros.

  - **AI 2 Absolute Value Min (V)**: Valor de tensión mínimo en la
        entrada analógica AI 2.
  - **AI 2 Absolute Value Max (V)**: Valor de tensión mínimo en la
        entrada analógica AI 2.
