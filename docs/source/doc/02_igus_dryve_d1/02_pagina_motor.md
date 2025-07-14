# Página "Motor"

La página de configuración "Motor" se muestra en la
{numref}`fig:conf_stepper_2`. A continuación se
describen las distintas opciones disponibles en esta página y como deben
ser establecidas.

:::{figure} images/config-stepper/02-motor.png
:name: fig:conf_stepper_2

Página de configuración de "motor" del controlador del motor paso a paso. 
:::

(sec:motor_motor)=
## Motor

- **Motor Type**: El tipo de motor, en nuestro caso seleccionamos
    "EC/BLDC (Brush-Less DC Motor)" para el motor sin escobillas, o
    "ST (Stepper Motor)" para el motor paso a paso.

- **Article Number**: Para motores Igus podemos seleccionar el número
    de articulo del motor. En este caso los parámetros "Motor
    Current", "Boost Current", "Holding Current", "Step Angle", y
    "Pole pairs", así como los demás parámetros de las secciones
    "Gear", "Feedback", "Closed Loop", "Brake", y "Braking
    Resistor", se rellenan automáticamente con los valores por defecto
    correspondientes al modelo de motor seleccionado.

    En el montaje de prueba, como estamos usando otros motores, hemos
    seleccionado "Custom article".

- **Motor Current (A)**: Indica la corriente continua máxima
    permisible del motor durante movimientos continuos, i.e., excepto en
    las fases de aceleración y desaceleración (ver la opción "Boost
    Current" para estos casos). Los valores posibles son de 0 A \-- 7
    A.

    :::{important}
    Este parámetro debe ser menor que la corriente máxima que pueda
    proporcionar la fuente de alimentación, teniendo también en cuenta
    las demás posibles cargas a las que deba suministrar potencia la
    fuente.
    :::

    En el montaje de prueba, como ambos motores son pequeños, no tienen
    ninguna carga que mover, y la fuente de alimentación usada
    proporciona un máximo de 2A, hemos establecido valores pequeños en
    este parámetro: 0.3 A para el motor paso a paso y 1 A para el motor
    sin escobillas.

- **Boost Current (A)**: Corriente de refuerzo. Indica la corriente
    máxima permisible del motor durante las fases de aceleración y
    deceleración. Durante estas fases, es posible un aumento de la
    corriente motor establecida en el parámetro "Motor Current" hasta
    el valor de la corriente de refuerzo durante un máximo de 2 s. La
    activación de la corriente de refuerzo depende de la frecuencia de
    movimiento. Los valores posibles son desde el valor del parámetro
    "Motor Current" hasta el 150 % (para motores paso a paso) o el 300
    \% (para motores sin escobillas) del valor del parámetro "Motor
    Current".

    :::{important}
    Al igual que en el parámetro anterior, este parámetro debe ser menor
    que la corriente máxima que pueda proporcionar la fuente de
    alimentación, teniendo también en cuenta las demás posibles cargas a
    las que deba suministrar potencia la fuente.
    :::

    En el montaje de prueba, al igual que en el parámetro anterior,
    hemos establecido valores pequeños en este parámetro: 0.5 A para el
    motor paso a paso y 1 A para el motor sin escobillas.

- **Holding Current (A)**: Corriente de retención. Ajusta la corriente
    aplicada al motor si está parado. Solo aplicable al caso de motores
    paso a paso en circuito de bucle abierto, en otro caso el parámetro
    estará deshabilitado y aparecerá sombreado en gris.

    En el montaje de prueba hemos configurado el controlador en bucle
    cerrado, por lo que esta opción está deshabilitada.

- **Step Mode**: Modo de paso. Solo aplicable en motores paso a paso,
    en otro caso el parámetro estará deshabilitado y aparecerá sombreado
    en gris. Este parámetro permite configurar la técnica de
    "microstepping" para controlar el motor
    {cite}`electricmotorsanddrives,enwiki:1166298756`. En lugar de mover el motor un paso completo a la vez
    (modo de paso 1/1), la técnica de microstepping divide cada paso en
    fracciones más pequeñas, lo que permite un mayor número de
    posiciones intermedias. Los modos disponibles son "Auto", 1/1
    (paso completo), 1/2, 1/4, 1/8, 1/16, 1/32, y 1/64.

    Cuanto menor sea el paso, más preciso será el posicionamiento, mejor
    será la estabilidad del movimiento, y menos ruido se emitirá, pero
    por otra parte la velocidad máxima teórica disminuirá. Por ejemplo,
    para un motor con un ángulo de paso de 1.8°, en modo de paso 1/1 se
    necesitan 200 pasos para completar un giro. En general, para un
    ángulo de paso $\theta$ y modo de paso $1/N$ se necesitan
    $360N/\theta$ pasos para completar un giro. Considerando que el
    controlador puede procesar pulsos de paso con un período de pulso
    mínimo $T$, la velocidad máxima teórica del motor en rpm será de
    $60\theta/(360NT) = \theta/(6NT)$. Es decir, para un modo de paso
    $1/N$, la velocidad máxima teórica se verá reducida por un factor
    $N$ con respecto a la velocidad máxima teórica del modo 1/1.

    La documentación del Igus dryve D1 especifica un período mínimo de
    pulso de paso de 40 μs. Sin embargo, el período mínimo real es
    menor. Utilizando un generador de señales y un osciloscopio hemos
    comprobado que el período mínimo real de pulso admitido por el Igus
    dryve D1 es de 4 μs. En la {numref}`tab:step_modes` se muestran para cada modo de paso los pasos por
    revolución y las máximas velocidades teóricas en rpm considerando un
    ángulo de paso de 1.8° y un período de pulso de paso mínimo de 4 μs.
    Es importante destacar que las velocidades mostradas en la tabla son
    velocidades teóricas calculadas a partir de la formula
    $\theta/(6NT)$, en la práctica los motores paso a paso no están
    pensados para llegar a altas velocidades. La máxima velocidad de un
    motor paso a paso dependerá del modelo de motor, pero normalmente la
    velocidad máxima de estos motores no será superior a 1000 rpm.

    En el montaje de prueba hemos establecido el modo de paso 1/32.

  :::{csv-table} Modos de paso, pasos por revolución, y máximas velocidades teóricas en rpm considerando un ángulo de paso de 1.8° y un período de pulso de paso mínimo de 4 µs.
  :class: align-col1-r, align-col2-r, align-col3-r
  :name: tab:step_modes
  :header: Modo de paso, Pasos por revolución, Máxima velocidad (rpm)
  :widths: auto

  1, 200, 75000
  1/2, 400, 37500
  1/4, 800, 18750
  1/8, 1600, 9370
  1/16, 3200, 4680
  1/32, 6400, 2340
  1/64, 12800, 1170
  :::

- **Step Angle**: Ángulo de paso. Solo disponible para motores paso a
    paso. El ángulo de paso indica el ángulo de un paso completo del
    motor (e.g., 0.72°, 0.9°, 1.8°). Esto es un parámetro físico del
    propio motor y determina el número de pasos completos por
    revolución, e.g., un motor con un ángulo de paso de 1.8° necesita
    $360/1.8 = 200$ pasos completos por revolución.

    En el montaje de prueba el motor paso a paso usado tiene un ángulo
    de paso de 1.8°.

- **Pole Pairs**: Pares de polos. Solo disponible para motores sin
    escobillas. Indica el número y la disposición de las bobinas del
    motor. Es un parámetro físico del propio motor.

    En el montaje de prueba el motor sin escobillas usado tiene 4 pares
    de polos.

Una vez rellenados los campos de esta sección deberemos hacer clic en el
botón "Apply Changes".

## Gear

Si el motor dispone de un engranaje reductor, este se puede configurar
en esta sección. Estableceremos esta opción a "OFF".

:::{note}
Estableceríamos esta opción a "OFF" aunque el motor dispusiera de
engranaje reductor. Esta opción solo sería necesaria si quisiéramos que
el controlador controlara la posición de su eje, pero como se comentó en
{numref}`sec:conf_start`, en nuestro caso no lo
necesitamos, ya que de esto se encargará LinuxCNC, solo necesitamos que
el controlador responda a las señales de movimiento que le mandemos.
Esto además puede facilitar la configuración de los parámetros de
movimiento del motor en las páginas "Axis" (ver
{numref}`sec:page_axis`) y "Drive Profile"
(ver {numref}`sec:page_drive_profile`).
:::

## Feedback

Esta sección permite configurar los parámetros del encoder conectado al
controlador. Si en el parámetro "Article Number" de la sección
"Motor" hemos seleccionado un motor de Igus, los parámetros de esta
sección ya estarán establecidos a sus valores correctos.

En el montaje de prueba hemos establecido los siguientes valores, de
acuerdo con las especificaciones de los encoders correspondientes:

- **Motor paso a paso**
  - **Tipo**: Encoder as a Line Driver
  - **Index**: ON
  - **Impulses**: 1000
- **Motor sin escobillas**
  - **Tipo**: Encoder as Single Ended
  - **Index**: ON
  - **Impulses**: 512

:::{important}
El botón "Impulse Check" hace al controlador comprobar automáticamente
el número de impulsos del encoder. Para esto hace girar una revolución
el motor, incluso aunque la señal "enable" no esté activada. Por lo
tanto, es importante no hacer clic en este botón si el motor no puede
girar libremente.
:::

## Closed Loop

Mediante el control de bucle cerrado el controlador compara la
información de posición recibida del encoder con el valor de referencia
deseado y ajusta el motor en función de esa comparación. Esta
retroalimentación continua permite corregir errores, manteniendo el
motor en la posición, velocidad, o estado deseado, y adaptarse a las
variaciones de carga de manera más eficiente, lo que resulta en un
control preciso y estable del motor, reduciendo considerablemente su
consumo de energía y su temperatura de funcionamiento.

Establecemos esta opción a "ON".

:::{important}
Para el control de bucle cerrado, el Igus dryve D1 utiliza internamente
dos controladores PIs para controlar la corriente y la velocidad,
respectivamente, y un controlador P para controlar la posición. Los
parámetros de estos controladores se muestran en la página
"Oscilloscope" (ver {numref}`sec:oscilloscope_parameters`). Si se pulsa en el botón "Self Tuning" de esta
sección, el controlador intentará determinar automáticamente los valores
de los parámetros de estos controladores.
:::

## Brake

El Igus dryve D1 puede controlar un freno de retención. Ninguno de los
motores que tenemos dispone de freno así que establecemos esta opción a
"OFF".

## Braking Resistor

Esta sección solo es aplicable al caso de motores sin escobillas. Estos
motores, al desacelerar, funcionan como generadores de potencia. Esto
puede producir picos de tensión mayores que la tensión de carga
aplicada, lo cual puede causar la destrucción del controlador, sobre
todo en el caso de altas desaceleraciones. Para evitar daños al
controlador, se debe utilizar una resistencia de frenado para disipar la
energía excesiva generada. Por lo tanto, es importante que cada
controlador que accione un motor sin escobillas esté equipado con su
propia resistencia de frenado.

El valor de la resistencia y su capacidad de disipación de potencia
dependen del motor usado. El manual del controlador proporciona los
detalles de como obtener estos valores a partir de los datos del motor.
En el montaje de prueba hemos usado una resistencia de 33 Ω con una
potencia de disipación máxima a 25 °C de 50 W (con disipador estándar) o
14 W (sin disipador).

Esta sección proporciona un único parámetro "Braking Voltage (V)", que
establece el umbral de tensión para aplicar la resistencia de frenado y
disipar el exceso de energía. Para una operación segura, el controlador
considera una histéresis de 1 V, de forma que la resistencia de frenado
se activará cuando la tensión del motor llegue a la tensión umbral más 1
V, y se detendrá cuando baje hasta la tensión umbral menos 1 V.

El umbral de tensión establecido en el parámetro "Braking Voltage"
debe ser un valor ligeramente superior a la tensión de alimentación del
motor, por ejemplo, si la tensión de alimentación del motor es 24 V un
umbral adecuado puede ser 26 V, si la tensión de alimentación del motor
es 48 V, un umbral adecuado puede ser 51 V. Un valor demasiado alto
podría causar que se disipase poca energía y causar el error "E09 Load
Supply High" (ver el manual del controlador, Sección 7: Alerts and
Errors).

En el montaje de prueba el motor sin escobillas usado estaba alimentado
a 24 V, así que hemos establecido este parámetro a 26 V.
