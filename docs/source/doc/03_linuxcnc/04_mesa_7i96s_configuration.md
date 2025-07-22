# MESA 7I96S Board Configuration

## Flashing the Firmware

:::{note}
This process has already been completed and does not need to be repeated; it is described here solely for documentation purposes. For more information on configuring the MESA 7I96S board, please consult its manual.
:::

The MESA 7I96S board can be used standalone with its standard configuration. However, to use it with the MESA 7I77 board, we must flash the FPGA with the appropriate firmware. Various firmwares for the 7I96S board are available on the MESA website at <http://www.mesanet.com/software/parallel/7i96s.zip>.

To use the MESA 7I96S board with the MESA 7I77 board, we will use the `7i96s_7i77d.bin` firmware. First, power the board with 5 V via its P4 connector and connect it to the PC using an Ethernet cable. By default, the board's IP address is `192.168.1.121`. To verify connectivity, execute the following command:

```sh
mesaflash -device 7i96s -addr 192.168.1.121
```

If successful, the `mesaflash` utility will detect the board and respond with the following output:

```text
ETH device 7I96S at ip=192.168.1.121
```

Finally, to flash the firmware to the board, execute the following command:

```sh
mesaflash -device 7i96s -addr 192.168.1.121 -write 7i96s_7i77d.bin
```

## IP Address

The MESA 7I96S board has three options for setting the IP address: a default IP (`192.168.1.121`), an IP read from the EEPROM, and IP acquisition via the BOOTP network protocol. These options are selected using jumpers `W4` and `W5`, located on the bottom left of the board as shown in {numref}`fig:mesa_ip_selection`.

:::{figure} images/mesa/mesa_7i96s_bottom_left_labelled.*
:name: fig:mesa_ip_selection

View of the bottom left side of the MESA 7I96S board.
:::

The available IP configuration options are detailed in {numref}`tab:mesa_ip_selection`. Specifically, note the following:

- When jumpers `W4` and `W5` are in the (down, up) position, the IP address will be read from the EEPROM. The default IP address in the EEPROM is 10.10.10.10. This IP address can be changed using the `mesaflash` utility. For example, to set the IP in the EEPROM to 10.10.10.100, you would execute the following command:

    ```sh
    mesaflash -device 7i96s -addr 192.168.1.121 -set ip=10.10.10.100
    ```

- When jumpers `W4` and `W5` are in the (up, up) position, the IP address will be set to 192.168.1.121, and the board will boot using the fallback configuration (see {numref}`sec:mesa7i96s_fallback`).

:::{csv-table} IP address configuration options on the MESA 7I96S board using jumpers ``W4`` and ``W5``.
:name: tab:mesa_ip_selection
:widths: auto
:header: W4, W5, IP Address

Down, Down, 192.168.1.121
Down, Up, Read from EEPROM
Up, Down, Obtained via BOOTP
Up, Up, 192.168.1.121 and use fallback conf.
:::

In our testbed setup, jumpers `W4` and `W5` have been set to the (down, up) position, as shown in {numref}`fig:mesa_ip_selection`. This configuration allows the board to read the IP address stored in the EEPROM. For this setup, we have configured the board's IP address to 10.68.33.122.

(sec:mesa7i96s_fallback)=
## Fallback Configuration

The MESA 7I96S board's flash memory contains two images: a main image and a fallback image. If the primary image becomes corrupted, the FPGA will load the fallback configuration, allowing a new main image to be written. Otherwise, the memory would have to be programmed via JTAG.

It is possible to force the board to boot using the fallback configuration by setting the IP selection jumpers `W4` and `W5` to the (up, up) position. In this boot mode, the card's IP address will be set to 192.168.1.121.

(sec:mesa7i96s_cable_power)=
## Expansion Connector 5 V Power Supply

The MESA 7I96S board has the capability to supply 5V power to the board connected to its expansion connector (P1), which in our case is the MESA 7I77. This option is controlled by jumper `W6`, located on the bottom of the board to the left of the expansion connector, as shown in {numref}`fig:mesa_ip_selection`. The settings are as follows:

- When jumper `W6` is in the up position, the MESA 7I96S board will provide power to the MESA 7I77 board through the expansion connector.
- When jumper `W6` is in the down position, the MESA 7I96S board will not provide power through the expansion connector; in this case, external power must be supplied to the MESA 7I77 board.

In our testbed setup, the latter option was chosen, with jumper `W6` configured in the down position, as seen in {numref}`fig:mesa_ip_selection`. The MESA 7I77 board must also be configured appropriately, as explained in {numref}`sec:mesa7i77_power`.
