(sec:conf_start)=
# Página "Start"

La página de configuración "Start" se muestra en la
{numref}`fig:conf_stepper_1`. Esta página
contiene diversos ajustes generales. En particular, estableceremos las
siguientes opciones en todos los controladores:

- **Measuring system**: Metric, Millimeter
- **Movement type**: Rotary
- **Time units**: Seconds

:::{figure} images/config-stepper/01-start.png
:name: fig:conf_stepper_1

Página de configuración inicial del controlador del motor paso a paso.
:::

:::{note}
Hemos configurado la opción de tipo de movimiento (*Movement type*) como
rotatorio (*Rotary*) aunque el motor mueva un eje lineal. Esto es porque
en nuestro caso no necesitamos que el controlador controle la posición
del eje, ya que de esto se encargará LinuxCNC, solo necesitamos que
responda a las señales de movimiento que le mandemos. Esto además puede
facilitar la configuración de los parámetros de movimiento del motor en
las páginas "Axis" (ver {numref}`sec:page_drive_profile`).
:::

Además, esta página también tiene las siguientes secciones:

- **Configuration**: Permite guardar la configuración actual del
    controlador a archivo y cargar una configuración desde archivo. Una
    vez se haya terminado de definir la configuración del controlador se
    recomienda usar esta funcionalidad para guardarla en un archivo.
- **Firmware**: Permite actualizar el firmware del controlador. El
    botón "Search" dirige a la URL de descarga de la última versión
    del firmware. El botón "Update" permite cargar el archivo de
    firmware desde disco para actualizar el controlador.
- **Password**: Permite establecer contraseña para los usuarios
    "Admin" (administrador) y "Guest" (invitado). Los usuarios
    pueden activarse o desactivarse con los interruptores
    correspondientes. Si ambos usuarios están desactivados (valor por
    defecto), se accede a la interfaz de usuario como "Admin". El
    usuario "Guest" sólo puede activarse si previamente se ha activado
    el usuario "Admin".
