# MESA 7I77 Board Configuration

(sec:mesa7i77_power)=

## 5 V Main Power

The MESA 7I77 board can draw its main 5V power either from the MESA 7I96S board or through its `TB1` connector. This power is needed for the encoders, analog outputs, and the RS-422 interface. The main power mode for the MESA 7I77 is selected using jumper `W5` as follows:

1. If `W5` is in the left position, power is supplied via the MESA 7I96S board. In this case, jumper `W6` on the MESA 7I96S board must be set to the up position.
2. If `W5` is in the right position, power must be supplied to the board externally through the `TB1` connector. In this case, jumper `W6` on the MESA 7I96S board must be set to the down position to prevent it from supplying power to the daughterboard.

:::{attention}
Supplying power to the MESA 7I77 board through the `TB1` connector with jumper `W5` in the left position can potentially damage the MESA 7I77 board, the MESA 7I96S board, the connection cable, and even the PC.
:::

In our gantry robot system, we chose to power the MESA 7I77 board via the `TB1` connector; therefore:

- Jumper `W6` on the MESA 7I96S board has been set to the down position, as shown in {numref}`fig:mesa_ip_selection`.
- Jumper `W5` on the MESA 7I77 board has been set to the right position, as shown in {numref}`fig:mesa7i77_left`.

:::{figure} images/mesa/mesa_7i77_left.*
:name: fig:mesa7i77_left

View of the left side of the MESA 7I77 board installed in the gantry robot system.
:::

## Digital Inputs and Outputs Power

In addition to the 5V main power, the MESA 7I77 board also requires supplementary power for its digital inputs and outputs through the `TB2` connector (see Figures {numref}`%s <fig:installation>` and {numref}`%s <fig:mesa7i77_right>`). The pinout for the `TB2` connector is provided in {numref}`tab:mesa7i77_tb2`.

:::{csv-table} Connections of the ``TB2`` connector of the MESA 7I77 board.
:name: tab:mesa7i77_tb2
:widths: auto
:header: Pin, Signal, Function

1 (bottom), `VFIELD`, `FIELD POWER`
2, `VFIELD`, `FIELD POWER`
3, `VFIELD`, `FIELD POWER`
4, `VFIELD`, `FIELD POWER`
5, `VIN`, `FIELD I/O LOGIC POWER`
6, Not connected, --
7, Not connected, --
8 (top), Ground, Reference of `VIN` & `VFIELD`
:::

As indicated in {numref}`tab:mesa7i77_tb2`, the board requires two power inputs in this configuration:

- `VFIELD`: This input supplies power to the outputs and determines the logic levels of the inputs, with a range of 5 V to 28 V.
- `VIN`: This input provides power to the input/output logic, with a range of 8 V to 32 V.

If `VFIELD` is between 8 V and 28 V, the same source can be used to power `VIN`. The board includes jumper W1, which, when placed in the left position, connects `VIN` with `VFIELD`. To use `VFIELD` values outside the `VIN` range (e.g., 5 V), you must place W1 in the right position to disconnect `VIN` and `VFIELD`, allowing for separate power supplies for `VIN` and `VFIELD`.

:::{attention}
The voltage at `VFIELD` must have a maximum rise rate of 10 V/ms to prevent damage to the board. This is a limitation of MOSFET transistors {cite}`toshiba2018impacts, toshiba2018mosfets, nexperia2023power, bai2003analysis`. Therefore, `VFIELD` must be connected directly to the power supply without using switches in the circuit.
:::

As stated in {numref}`sec:page_input_outputs`, the MESA 7I96S board can only use 5 V logic for step and direction signals. Therefore, the logic for both the igus® dryve D1 controllers and the MESA 7I77 board must also be 5 V. Thus, in our gantry robot system, jumper `W1` on the MESA 7I77 board has been set to the right position, the `VIN` input to 24 V, and the `VFIELD` input to 5 V, as shown in {numref}`fig:mesa7i77_right`.

::: {figure} images/mesa/mesa_7i77_right.*
:name: fig:mesa7i77_right

View of the right side of the MESA 7I77 board installed in the gantry robot system.
:::

## Encoder Input Modes

The MESA 7I77 board has six encoder inputs, each with individual A, B, and Z inputs. These inputs can be configured to operate with either differential or single-ended signals. Each encoder has three jumpers to configure the mode for its individual A, B, and Z inputs. Setting a jumper to the right position selects differential mode, while setting it to the left position selects single-ended mode. The list of jumpers for the individual inputs of each encoder is provided in {numref}`tab:encoder_jumpers`.

:::{table} Encoder configuration jumpers.
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

In our gantry robot system each of the 4 motors has a differential encoder. Therefore, we set encoders 0 to 3 on the MESA 7I77 board to differential mode. {numref}`fig:mesa7i77_left` shows the location of the jumpers for encoders 0 to 3 on the MESA 7I77 board.
