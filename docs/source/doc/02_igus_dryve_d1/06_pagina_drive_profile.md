(sec:page_drive_profile)=
# Página "Drive Profile" 

Esta página permite seleccionar el modo de control para ejecutar
movimientos. Los modos disponibles son:

- **Binary**: Control de movimiento mediante entradas digitales o
    analógicas y salidas digitales.
- **Tipp/Teach**: Control de movimiento mediante entradas digitales o
    analógicas y salidas digitales. En este modo es posible modificar
    las posiciones objetivo de movimientos existentes usando las
    entradas digitales.
- **Step/Direction**: Control de movimiento a partir de señales de
    paso y dirección. Solo disponible para motores paso a paso.
- **CANopen**: Control de movimiento a través del protocolo de
    comunicación CANopen.
- **Modbus TCP**: Control de movimiento a través del protocolo de
    comunicación Modbus TCP.

A continuación describimos las configuraciones a aplicar a los motores.

## Motor paso a paso

En el caso del motor paso a paso seleccionamos el modo de control
"step/direction". En la {numref}`fig:conf_stepper_6` se muestra la página de configuración de "Drive
Profile" del controlador del motor paso a paso, usando el modo de
control "step/direction". Este modo de control no requiere de ninguna
configuración adicional, en la página se mostrará la información de uso
de las señales de paso y dirección.

:::{figure} images/config-stepper/06-drive_profile.png
:name: fig:conf_stepper_6

Página de configuración de "Drive Profile" del controlador del motor paso a paso, usando el modo de control "step/direction".
:::

## Motor sin escobillas

En el caso del motor sin escobillas seleccionamos el modo de control
"binary". En la {numref}`fig:conf_brushless_6` se muestra la página de configuración "Drive Profile"
del controlador del motor sin escobillas, usando el modo de control
"binary". Este modo proporciona una tabla de movimientos (ver la
{numref}`fig:conf_brushless_6`) que permite
programar hasta 32 movimientos parametrizados con el modo de movimiento,
el objetivo, la aceleración máxima, la velocidad, y el número del
siguiente movimiento a ejecutar. Para el caso del motor sin escobillas
introducimos un único movimiento en la posición 1 usando el modo ADR
(Analogue Rotation with Direction Definition). El modo ADR permite
realizar movimientos rotatorios estableciendo su velocidad en la entrada
analógica AI 1.

:::{figure} images/config-brushless/06-drive_profile.png
:name: fig:conf_brushless_6

Página de configuración de "Drive Profile" del controlador del motor sin escobillas, usando el modo de control "binary".
:::

En el montaje de prueba hemos establecido los siguientes parámetros para
el movimiento de la posición 1:

- **Mode**: ADR (Analogue Rotation with Direction Definition).
- **Goal (°)**: Lo dejaremos vacío.
- **Acceleration (°/s{sup}`2`)**: 50000 °/s{sup}`2`, que equivalen a 138.89
    rev/s{sup}`2`.
- **Velocity (°/s)**: 18000 °/s, que equivalen a 3000 rpm.
- **Deceleration (°/s{sup}`2`)**: 50000 °/s{sup}`2`, igual que la aceleración.
- **Pause (ms)**: Lo dejaremos vacío.
- **Next**: Lo dejaremos vacío.

Como se explicó en la {numref}`sec:page_input_outputs`, la entrada analógica AI 1 se configuró para estar en un
rango de ±10 V. El controlador variará la velocidad del motor de de
manera proporcional a la señal analógica aplicada. Así, cuando la
entrada AI 1 se establezca a -10 V, el motor girará a 3000 rpm en
sentido antihorario, mientras que al ajustarla a 10 V, el motor girará a
3000 rpm en sentido horario.

Una vez configurado el movimiento, es necesario activarlo para que el
controlador mueva el motor. Para esto hay dos posibilidades:

1. Seleccionar el movimiento haciendo clic en la fila número 1 de la
    tabla de movimientos y a continuación hacer clic en el botón
    "start" en la parte de abajo de la página.
2. Mediante las entradas y salidas digitales del controlador.

El punto 1 puede ser adecuado para realizar pruebas, pero para un
sistema final es necesario implementar el punto 2. En este caso,
considerando un controlador encendido y con la señal "enable" no
activada, los pasos a seguir son los siguientes:

1. Establecer las entradas digitales 1 a 5 (X2.1 a X2.5) con el número
    del movimiento seleccionado menos uno, donde la entrada 1 representa
    el bit menos significativo y la entrada 5 el más significativo. Por
    ejemplo, para el número 1 las entradas se establecerán a 00000; para
    el 2 a 00001; y así sucesivamente, hasta 32 que se establecerá
    a 11111. Para el movimiento número 1, que es nuestro caso,
    simplemente se pueden dejar las entradas digitales 1 a 5
    desconectadas.
2. Establecer la entrada digital 7 (X2.7, entrada "enable") a nivel
    alto.
3. Una vez activada la entrada "enable", esperar a que el controlador
    establezca a nivel alto la salida digital 1 (X3.1, salida
    "ready"). Esta salida indica que el controlador está listo para
    aceptar comandos de posición.
4. Una vez esté activada la salida "ready", enviar un pulso
    rectangular a la entrada digital 6 (X2.6, señal "start") para
    inicial el programa de movimiento. El controlador dispone de un
    filtro anti-rebote con un tiempo de 10 ms en las entradas digitales
    1 a 10 (excepto en las entradas de paso y dirección), por lo que el
    pulso debe tener una longitud superior a 10 ms para que el
    controlador lo detecte. En el montaje de prueba hemos establecido la
    duración del pulso a 100 ms.

En el montaje de prueba, el proceso de activación del movimiento se ha
configurado en LinuxCNC y se realiza mediante la placa MESA 7I77, que es
la que envía y recibe las señales correspondientes.
