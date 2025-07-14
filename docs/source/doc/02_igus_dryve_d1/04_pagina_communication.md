(sec:page_communication)=
# Página "Communication" 

La página de configuración "Communication" se muestra en la
{numref}`fig:conf_stepper_4`. Esta página
permite configurar las comunicaciones mediante Ethernet y los sistemas
bus del controlador. A continuación se describen las distintas opciones
disponibles en esta página y como deben ser establecidas.

:::{figure} images/config-stepper/04-communication.png
:name: fig:conf_stepper_4

Página de configuración de "comunicación" del controlador del motor paso a paso.
:::

## Ethernet TCP/IP

Esta sección permite configurar los parámetros de conexión TCP/IP:
dirección IP, mascara de subred, puerta de acceso, y nombre del host.
Una vez establecidos los parámetros se debe pulsar el botón "Reload"
para aplicar los cambios.

En el montaje de prueba se han establecido estos parámetros de forma
manual a los valores mostrados en la
{numref}`tab:conf_ethernet`. Los controladores
se han conectado mediante un conmutador (switch) con un PC portátil. Los
parámetros se establecieron para que fuera posible conectar el sistema a
la red del laboratorio, aunque esto no se llegó a hacer.

:::{csv-table} Parámetros de configuración Ethernet.
:name: tab:conf_ethernet
:widths: auto
:header: Parámetro,Motor paso a paso,Motor sin escobillas

IP-Address,  10.68.33.120,       10.68.33.121
Subnet Mask, 255.255.252.0,      255.255.252.0
Gateway,     10.68.32.1,         10.68.32.1
Hostname,    igus-dryve-D1-098a, igus-dryve-D1-098e
:::

## Transmission Protocol

Esta sección permite seleccionar si la comunicación con el servidor web
del controlador dryve D1 debe hacerse mediante una conexión http no
cifrada o una conexión https cifrada. En el caso de una conexión https
se puede suministrar un certificado externo o generar un certificado
autofirmado.

En el montaje de prueba se ha seleccionado la opción de usar una
conexión http no cifrada.

## Bus Systems

El controlador dispone de dos sistemas de buses, CANopen y Modbus, que
permiten comunicarse con el controlador y controlar el movimiento del
motor. En nuestro caso no usaremos ninguno de estos sistemas, ya que
controlaremos el motor mediante las entradas y salidas de los conectores
X2 (entradas digitales), X3 (salidas digitales), y X4 (entradas
analógicas). Por lo tanto se han dejado las opciones "CANopen" y
"Modbus TCP Gateway" al valor por defecto "OFF".
