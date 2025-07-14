(sec:page_oscilloscope)=
# Página "Oscilloscope" 

La página "Oscilloscope" se muestra en la
{numref}`fig:conf_brushless_7`. Esta página
ofrece dos funcionalidades esenciales para el ajuste y la monitorización
del rendimiento del motor: el osciloscopio interno y la configuración de
los parámetros del control de bucle cerrado del motor.

:::{figure} images/config-stepper/07-oscilloscope.png
:name: fig:conf_brushless_7

Página de configuración de "Oscilloscope" del controlador del motor paso a paso.
:::

## Osciloscopio

El osciloscopio permite la observación simultánea de 4 canales durante
un período de 5 segundos, permitiendo una evaluación detallada del
comportamiento del motor en tiempo real. Cada canal puede monitorizar
uno de los siguientes valores:

- Corriente actual (A)
- Error de seguimiento
- Velocidad (rpm)
- Posición actual
- Posición deseada
- Entradas digitales
- Entrada analógica 1 (AI 1)
- Entrada analógica 2 (AI 2)

(sec:oscilloscope_parameters)=
## Parámetros de control 

:::{figure} images/motor_control/fig.*
:name: fig:motor_control

Control en bucle cerrado de posición, velocidad, y corriente.
:::

El manual del controlador Igus dryve D1 no describe el sistema de
control que implementa, pero podemos asumir que emplea un sistema de
control de bucle cerrado con "minor loop feedback compensation"
{cite}`enwiki:1032838404,nise2015control,golnaraghi2017automatic`. En este sistema, la posición, velocidad, y corriente del
motor se utilizan como señales de realimentación para ajustar de manera
precisa y dinámica su posición. Este es un sistema de control
típicamente usado en control de motores. Su estructura, considerando los
parámetros P e I definidos por el controlador Igus dryve D1, se muestra
en en la {numref}`fig:motor_control`, donde:

- $R(t)$ es la posición solicitada para el motor en el instante $t$.

- $c(t)$ es la corriente suministrada al motor en el instante $t$,
    usada como parámetro de realimentación para el controlador de
    corriente.

- $p(t)$ es la posición del motor en el instante $t$, obtenida del
    "encoder" del motor y usada como parámetro de realimentación para
    el controlador de posición.

- $v(t)$ es la velocidad del motor en el instante $t$, obtenida como
    la derivada respecto de $t$ de la posición $p(t)$ y usada como
    parámetro de realimentación para el controlador de velocidad.

- $e_c(t)$ es el error de corriente, obtenido como la salida del
    controlador de velocidad menos el parámetro de realimentación de
    corriente $c(t)$.

- $e_p(t)$ es el error de posición, obtenido como $R(t) - p(t)$.

- $e_v(t)$ es el error de velocidad, obtenido como la salida del
    controlador de posición menos el parámetro de realimentación de
    velocidad $v(t)$.

- $\kappa_p$ es el parámetro proporcional para el controlador de
    posición.

- $\lambda_p$ y $\lambda_i$ son respectivamente los parámetros
    proporcional e integral para el controlador de velocidad.

- $\mu_p$ y $\mu_i$ son respectivamente los parámetros proporcional e
    integral para el controlador de corriente.

- $P(\alpha)(t)$ es la respuesta al impulso del bloque proporcional.
    Para una entrada $x(t)$ la salida del bloque proporcional en el
    instante $t$ es

    $$x(t) * P(\alpha)(t) = \alpha \cdot x(t)$$

- $I(\beta)(t)$ es la respuesta al impulso del bloque integral. Para
    una entrada $x(t)$ la salida del bloque integral en el instante $t$
    es

    $$x(t) * I(\beta)(t) = \beta \int_{-\infty}^t x(\tau) d\tau$$

La página "Oscilloscope" proporciona acceso a la configuración de los
parámetros de control de los controladores PIs. Con estos parámetros
podemos optimizar el rendimiento del motor para satisfacer las
necesidades específicas de cada tarea. En el caso de motores de Igus, al
seleccionar el modelo del motor correspondiente en la sección de
configuración del motor (ver {numref}`sec:motor_motor`), los parámetros de control se establecerán a los valores
por defecto para el motor seleccionado. En aplicaciones con velocidades
elevadas, cargas pesadas, o cuando sea necesario minimizar el ruido,
podría ser necesario realizar ajustes finos a la configuración de los
parámetros de control.

En el montaje de prueba hemos configurado los siguientes parámetros para
ambos motores, que parecen funcionar bien:

- **Current**
  - **Amplification (P)**: 20
  - **Time constant (I)**: 1000
- **Velocity**
  - **Amplification (P)**: 0.1
  - **Time constant (I)**: 0
- **Position**
  - **Amplification (P)**: 1000

:::{note}
Es importante tener en cuenta los siguientes puntos cuando configuremos
los parámetros de control de los motores:

- Los parámetros se hacen efectivos al pulsar "enter" o quitar el
    foco de la entrada del parámetro correspondiente.
- Los parámetros se deben ajustar muy finamente, un cambio brusco en
    un parámetro puede hacer que el controlador PI correspondiente se
    vuelva inestable y causar un movimiento brusco del motor. En este
    caso si hemos configurado adecuadamente los parámetros del límites
    de movimiento (ver {numref}`sec:axis_motion_limits`) el controlador debería parar el motor y dar un error
    de seguimiento.
- Ajustar algunos de los parámetros a un valor demasiado alto podría
    provocar vibraciones y ruidos no deseados en los motores provocados
    por oscilaciones en la señal del controlador PI. Por otra parte,
    ajustar algunos de los parámetros a valores demasiado bajos podría
    provocar que los motores respondieran de forma lenta a los
    movimientos comandados por el controlador.
:::
