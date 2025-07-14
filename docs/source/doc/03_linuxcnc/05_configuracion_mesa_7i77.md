# Configuración de la placa MESA 7I77

(sec:mesa7i77_power)=
## Alimentación principal de 5 V

La placa MESA 7I77 puede obtener su alimentación principal a través de
la placa MESA 7I96S, o a través de su conector `TB1`. Esta alimentación
debe ser de 5 V y se usa para alimentar los encoders, las salidas
analógicas, y la interfaz RS-422. El modo de la alimentación principal
en la MESA 7I77 se selecciona mediante el jumper `W5` de la siguiente
forma:

1. Si `W5` está en la posición izquierda, la alimentación se obtiene a
    través de la placa MESA 7I96S, en este caso el jumper `W6` de la
    placa MESA 7I96S deberá establecerse en la posición arriba.
2. Si `W5` está en la posición derecha, se debe suministrar la
    alimentación a la placa mediante el conector `TB1`, en este caso el
    jumper `W6` de la placa MESA 7I96S deberá establecerse en la
    posición abajo para que no proporcione energía a la placa hija.

:::{attention}
Suministrar alimentación a la placa MESA 7I77 a través del conector
`TB1` con el jumper `W5` en la posición izquierda puede dañar la placa
MESA 7I77, la placa MESA 7I96S, el cable de conexión, e incluso el PC.
:::

En el montaje de prueba se ha escogido alimentar a la placa MESA 7I77 a
través del conector `TB1`, por lo que:

- El jumper `W6` de la placa MESA 7I96S se ha establecido en la
    posición abajo. Esto se puede ver en la
    {numref}`fig:mesa_ip_selection`.
- El jumper `W5` de la placa MESA 7I77 se ha establecido en la
    posición derecha. Esto se muestra en la
    {numref}`fig:mesa7i77_left`.

:::{figure} images/mesa/mesa_7i77_left_labelled.*
:name: fig:mesa7i77_left

Vista de la parte izquierda de la placa MESA 7I77.
:::

## Alimentación de las entradas y salidas digitales

Aparte de la alimentación principal de 5 V, la placa MESA 7I77 también
necesita alimentación adicional para las entradas y salidas digitales a
través del conector `TB2` (ver Figuras
{numref}`%s <fig:gantry_installation>` y
{numref}`%s <fig:mesa7i77_right>`). El listado
de conexiones del conector `TB2` se reproduce en la
{numref}`tab:mesa7i77_tb2`.

:::{csv-table} Conexiones del conector ``TB2`` de la placa MESA 7I77.
:name: tab:mesa7i77_tb2
:widths: auto
:header: Pin, Señal, Función

  1 (abajo), `VFIELD`, `FIELD POWER`
  2, `VFIELD`, `FIELD POWER`
  3, `VFIELD`, `FIELD POWER`
  4, `VFIELD`, `FIELD POWER`
  5, `VIN`, `FIELD I/O LOGIC POWER`
  6, No conectado, \--
  7, No conectado, \--
  8 (arriba), Tierra, Referencia de `VIN` & `VFIELD`
:::

Como se puede ver en la {numref}`tab:mesa7i77_tb2`, en este caso la placa requiere de dos entradas de
alimentación:

- `VFIELD`: Esta entrada proporciona la alimentación de las salidas y
    determina los niveles lógicos de las entradas. Entre 5 V \-- 28 V.
- `VIN`: La alimentación para la lógica de las entradas y salidas.
    Entre 8 V \-- 32 V.

Si `VFIELD` está entre 8 V \-- 28 V, puede usarse la misma fuente para
alimentar a `VIN`. Para esto la placa incluye el jumper W1, que al
colocarlo en la posición izquierda conecta `VIN` con `VFIELD`. Si
queremos usar valores de `VFIELD` fuera del rango de `VIN`, por ejemplo,
5 V, debemos colocar W1 en la posición derecha para desconectar `VIN` e
`VFIELD`, de esta forma podemos usar fuentes de alimentación separadas
para `VIN` y `VFIELD`.

:::{attention}
La tensión en `VFIELD` debe tener una tasa de aumento máxima de 10 V/ms,
de lo contrario la placa puede sufrir daños. Esta es una limitación de
los transistores MOSFET
{cite}`toshiba2018impacts, toshiba2018mosfets, nexperia2023power, bai2003analysis`. Por lo tanto, `VFIELD` debe conectarse directamente a la
fuente de alimentación sin usar interruptores, disyuntores, o contactos
de relé en el circuito. Un fusible es aceptable pero en ningún caso debe
conectarse `VFIELD` a través de un contacto mecánico.
:::

Como se comentó en la {numref}`sec:page_input_outputs`, la placa MESA 7I96S solamente puede usar lógica de 5 V
para las señales de paso y dirección, y por lo tanto, la lógica de los
controladores Igus dryve D1 y de la placa MESA 7I77 debe ser también a 5
V. De esta forma, en el montaje de prueba se ha establecido en la placa
MESA 7I77 el jumper `W1` en la posición derecha, la entrada `VIN` a 24
V, y la entrada `VFIELD` a 5 V. Esto se muestra en la
{numref}`fig:mesa7i77_right`.

::: {figure} images/mesa/mesa_7i77_right_labelled.*
:name: fig:mesa7i77_right

Vista de la parte derecha de la placa MESA 7I77.
:::

## Modos de entrada de los encoders

La placa MESA 7I77 dispone de seis entradas para encoders, cada una con
entradas individuales A, B, y Z. Estas entradas pueden configurarse para
funcionar con señales diferenciales o con señales de terminación única.
Cada encoder dispone de 3 jumpers para configurar el modo de las
entradas individuales A, B, y Z. En la posición derecha se selecciona el
modo diferencial, y en la posición izquierda el modo de terminación
única. El listado de jumpers para las entradas individuales de cada
encoder se muestra en la {numref}`tab:encoder_jumpers`.




:::{table} Jumpers de configuración de los encoders.
:name: tab:encoder_jumpers
:widths: auto
    
| Encoder   | Jumper A  | Jumper B | Jumper C |
| --------- | --------- | -------- | -------- |
| 0         | W21       | W19      | W17      |
| 1         | W15       | W13      | W10      |
| 2         | W8        | W6       | W2       |
| 3         | W22       | W20      | W18      |
| 4         | W16       | W14      | W11      |
| 5         | W9        | W7       | W3       |
:::

En el montaje de prueba se usaron las siguientes entradas y modos de
encoder de la placa MESA 7I77:

- En la entrada 0 se conectó el encoder del motor paso a paso. Este
    encoder es de señal diferencial, por lo que los jumpers `W21`,
    `W19`, y `W17` se dejaron en la posición derecha, esta es la
    posición de serie.
- En la entrada 1 se conectó el encoder del motor sin escobillas. Este
    encoder es de señal de terminación única, por lo que en este caso se
    establecieron los jumpers `W15`, `W13`, y `W10` en la posición
    izquierda.

La configuración de los jumpers anteriormente citados para los encoders
0 y 1 de la placa MESA 7I77 en el montaje de prueba se muestra en la
{numref}`fig:mesa7i77_left`.
