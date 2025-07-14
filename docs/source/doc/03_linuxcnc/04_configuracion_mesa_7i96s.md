# Configuración de la placa MESA 7I96S

## Flashear el firmware

:::{note}
Este proceso ya ha sido realizado, por lo tanto, no es necesario volver
a hacerlo, simplemente se describe aquí para que quede documentado. Para
más información acerca de la configuración de la placa MESA 7I96s
consultar su manual.
:::

La placa MESA 7I96S puede ser usada individualmente como viene de serie,
pero para ser usarla junto con la placa MESA 7I77 debemos flashear la
FPGA con el firmware adecuado. Los diferentes firmwares disponibles para
la placa 7I96S se proporcionan en la web de MESA en
<http://www.mesanet.com/software/parallel/7i96s.zip>.

Para usar la placa MESA 7I96S junto con la placa MESA 7I77 usaremos el
firmware `7i96s_7i77d.bin`. En primer lugar, deberemos alimentar la
placa con 5 V a través de su conector P4 y conectarla al PC mediante
Ethernet. Por defecto, la dirección IP de la placa es `192.168.1.121`,
para comprobar que podemos conectarnos con ella ejecutamos el siguiente
comando:

```sh
mesaflash -device 7i96s -addr 192.168.1.121
```

Si todo va bien, la utilidad `mesaflash` logrará detectar la placa y nos
responderá con la siguiente salida:

```text
ETH device 7I96S at ip=192.168.1.121
```

Finalmente, para flashear el firmware a la placa, ejecutamos el
siguiente comando:

```sh
mesaflash -device 7i96s -addr 192.168.1.121 -write 7i96s_7i77d.bin
```

## Dirección IP

La placa MESA 7I96S dispone de tres opciones para establecer la
dirección IP: IP por defecto (192.168.1.121), IP leída de la EEPROM, y
obtención de la IP mediante el protocolo de red BOOTP. Estas opciones se
seleccionan mediante los jumpers `W4` y `W5`, situados en la parte
inferior izquierda de la placa como se muestra en la
{numref}`fig:mesa_ip_selection`.

:::{figure} images/mesa/mesa_7i96s_bottom_left_labelled.*
:name: fig:mesa_ip_selection

Vista de la parte inferior izquierda de la placa MESA 7I96S.
:::

Las opciones de configuración de IP disponibles se detallan en la
{numref}`tab:mesa_ip_selection`. En particular
cabe destacar lo siguiente:

- Con los jumpers `W4` y `W5` en la posición (abajo, arriba) la
    dirección IP se leerá de la EEPROM. La dirección IP de serie en la
    EEPROM es 10.10.10.10. Esta dirección IP se puede cambiar mediante
    la utilidad `mesaflash`, por ejemplo para establecer la IP en la
    EEPROM a 10.10.10.100 ejecutaríamos el siguiente comando:

    ```sh
    mesaflash -device 7i96s -addr 192.168.1.121 -set ip=10.10.10.100
    ```

- Con los jumpers `W4` y `W5` en la posición (arriba, arriba) la
    direción IP se establecerá a 192.168.1.121 y la placa arrancará
    usando la configuración de respaldo (ver
    {numref}`sec:mesa7i96s_fallback`).

:::{csv-table}  Opciones de configuración de la dirección IP en la placa MESA 7I96S mediante los jumpers ``W4`` y ``W5``.
:name: tab:mesa_ip_selection
:widths: auto
:header: W4, W5, Dirección IP

Abajo, Abajo, 192.168.1.121
Abajo, Arriba, Leída de la EEPROM
Arriba, Abajo, Obtenida vía BOOTP
Arriba, Arriba, 192.168.1.121 y usar conf. de respaldo
:::

En el montaje de prueba se han establecido los jumpers `W4` y `W5` en la
posición (abajo, arriba) como se muestra en la
{numref}`fig:mesa_ip_selection`. De esta forma
la placa lee la dirección IP grabada en la EEPROM. En este caso hemos
establecido la dirección IP de la placa a 10.68.33.122.

(sec:mesa7i96s_fallback)=
## Configuración de respaldo

La memoria flash de la placa MESA 7I96S contiene dos imágenes, una
principal, y otra de respaldo. Si la imagen primaria se corrompe, la
FPGA cargará la configuración de respaldo, de esta forma se podrá grabar
una nueva imagen principal. De otra forma habría que programar la
memoria mediante JTAG.

Se puede forzar a que la placa arranque usando la configuración de
respaldo estableciendo los jumpers de selección de IP `W4` y `W5` a la
posición (arriba,arriba). Con este modo de arranque la dirección IP de
la tarjeta se establecerá a 192.168.1.121.

(sec:mesa7i96s_cable_power)=
## Alimentación de 5 V del conector de expansión

La placa MESA 7I96S tiene la opción de suministrar alimentación de 5V a
la placa conectada a su conector de expansión (P1), en nuestro caso la
MESA 7I77. Esta opción esta controlada por el jumper `W6`, situado en la
parte inferior de la placa a la izquierda del conector de expansión,
como se muestra en la {numref}`fig:mesa_ip_selection`, de forma que:

- Con el jumper `W6` en la posición arriba, la placa MESA 7I96S
    proporcionará alimentación a la placa MESA 7I77 a través del
    conector de expansión.
- Con el jumper `W6` en la posición abajo, la placa MESA 7I96S no
    proporcionará alimentación a través del conector de expansión,
    deberemos proporcionar alimentación externa a la placa MESA 7I77.

En el montaje de prueba se ha escogido esta última opción, configurando
el jumper `W6` en la posición abajo, como puede verse en la
{numref}`fig:mesa_ip_selection`. La placa MESA
7I77 también deberá configurarse adecuadamente como se explica en la
{numref}`sec:mesa7i77_power`.
