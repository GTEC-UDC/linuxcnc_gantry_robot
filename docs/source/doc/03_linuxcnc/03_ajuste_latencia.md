# Ajuste de la latencia del sistema

La latencia máxima del sistema puede depender de diversos factores como
el hardware, la configuración del firmware, la carga del sistema, o el
manejo de las interrupciones hardware. En el caso de que la latencia
máxima del sistema sea demasiado alto será necesario realizar cambios en
la configuración del sistema para reducirlo. Diversas fuentes,
incluyendo documentación oficial, guías, y charlas, proporcionan pautas
detalladas para ajustar el rendimiento de los sistemas Linux en tiempo
real
{cite}`redhat_rt_low_latency,ubuntu_rt_tuning,lfoss2022tips,elc2023preparing`. En el manual de usuario de LinuxCNC
{cite}`linuxcncdoc` también se indican varios
de los ajustes posibles para reducir la latencia, estos se describen en
las siguientes secciones.

En el montaje de prueba se empleó un portátil Lenovo T430s con CPU Intel
Core i5-3320M y sistema operativo Debian 12. Por otra parte, solo se ha
considerado el uso de un hilo lento con un período de 1 ms. Para este
caso, los valores de latencia obtenidos, como se muestra en las Figuras
{numref}`%s <fig:linuxcnc_latency_plot>`,
{numref}`%s <fig:linuxcnc_latency_test>`, y
{numref}`%s <fig:linuxcnc_latency_histogram>`,
fueron suficientemente bajos sin necesidad de ningún cambio adicional.
Sin embargo, si usáramos otro hardware, aún usando el mismo sistema
operativo, los valores de latencia podrían ser mayores y entonces sería
necesario cambiar algunas opciones del sistema para reducirlos. En caso
de que la latencia del sistema fuera demasiado elevada durante el uso de
LinuxCNC, este mostraría una advertencia similar a de la
{numref}`fig:linuxcnc_gui_axis_delay_warning`.

:::{figure} images/linuxcnc/linuxcnc_gui_axis_delay_warning.png
:name: fig:linuxcnc_gui_axis_delay_warning

Advertencia de LinuxCNC de valores de latencia inesperados.
:::

## Ajustes del firmware

El firmware del sistema, comúnmente en forma de BIOS o UEFI, puede tener
un impacto en la latencia del sistema. Este impacto puede variar según
el fabricante del hardware y la calidad del firmware que proporciona. El
firmware es responsable de inicializar y configurar el hardware del
sistema antes de que el sistema operativo se cargue. Si el firmware no
está configurado correctamente para proporcionar una temporización
precisa o no gestiona adecuadamente las interrupciones y los
dispositivos de hardware, puede contribuir a la latencia del sistema.

Los ajustes del firmware especificados en el manual de usuario de
LinuxCNC {cite}`linuxcncdoc` que pueden ayudar
a reducir la latencia son los siguientes:

- Desactivar la APM, la ACPI, y demás funciones de ahorro de energía.
    Esto incluye todo lo relacionado con la suspensión, escalado de
    frecuencia de la CPU, etc.
- Desactivar el modo "turbo" de la CPU.
- Desactivar la tecnología multihilo simultánea de la CPU, por
    ejemplo, en el caso de CPUs Intel, la tecnología Hyper-Threading.
- Desactivar o limitar las SMIs.
- Desactivar el hardware que no se vaya a utilizar.

## Ajustes de Linux

Linux dispone de opciones que pueden ayudar a mejorar la latencia. En
concreto, para nuestro caso consideraremos parámetros de línea de
comandos al iniciar el kernel y en tiempo de ejecución mediante el
comando `sysctl`. A continuación se describen estos parámetros.

### Parámetros de línea de comandos al iniciar el kernel

La lista completa de parámetros está disponible en
<https://docs.kernel.org/admin-guide/kernel-parameters.html>. En Debian,
los parámetros de línea de comando se pueden especificar de las
siguientes formas:

1. En el gestor de arranque GRUB, podemos pulsar la tecla para editar
    la entrada de arranque seleccionada y añadimos los parámetros al
    final de la línea, una vez añadidos podemos arrancar el sistema
    pulsando o .
2. Para especificar los parámetros de forma persistente, editamos el
    archivo `/etc/default/grub` añadiendo los parámetros a la variable
    `GRUB_CMDLINE_LINUX_DEFAULT` y a continuación ejecutamos el comando
    `update-grub`. Para más información acerca de las variables de
    configuración de GRUB ver la página correspondiente de su manual en
    <https://www.gnu.org/software/grub/manual/grub/html_node/Simple-configuration.html>.

Para el caso de la latencia, los parámetros más relevantes, sugeridos en
el manual de usuario de LinuxCNC {cite}`linuxcncdoc`, son los siguientes:

- `isolcpus`: Lista de CPUs que serán aisladas de los algoritmos de
    balanceo y planificación. Evita que la mayoría de los procesos del
    sistema utilicen las CPUs especificadas, dejando más tiempo de CPU
    disponible para LinuxCNC.
- `irqaffinity`: Lista de CPUs para establecer la máscara de afinidad
    irq por defecto. Selecciona las CPUs que servirán las
    interrupciones, de modo que las restantes CPUs no tengan que
    realizar esta tarea.
- `rcu_nocbs`: Lista de CPUs cuyas llamadas de retorno de RCU se
    ejecutarán en otras
    CPUs.{cite}`enwiki:1169786538,redhat_rt_rcu`.
- `rcu_nocb_poll`: Despertar los hilos de ejecución de las llamadas
    RCU periódicamente mediante un temporizador para comprobar si hay
    llamadas de retorno que ejecutar. Sin esta opción, las CPUs
    establecidas en `rcu_nocbs` son las responsables de despertar a los
    hilos encargados de ejecutar las llamadas RCU
    {cite}`redhat_rt_rcu`. Esta opción mejora
    la respuesta en tiempo real de las CPUs establecidas en `rcu_nocbs`
    al liberarlas de la necesidad de despertar los correspondientes
    hilos.
- `nohz_full`: Lista de CPUs a las que se dejará de enviar ticks de
    temporización cuando solo ejecuten una tarea. Como resultado, las
    CPUs pueden pasar más tiempo ejecutando las aplicaciones y menos
    tiempo atendiendo interrupciones y cambiando de contexto. Las CPUs
    de esta lista tendran sus llamadas de retorno de RCU transferidas a
    otras CPUs, como si hubieran sido establecidas en la opción
    `rcu_nocbs`.

Para ver el número de procesadores del sistema podemos usar el comando
`nproc` o el comando `cat /proc/cpuinfo`. Como ejemplo, para un sistema
con 4 CPUs, si queremos aislar 3 CPUs de perturbaciones, podemos usar
los siguientes parámetros:

```text
isolcpus=1-3 nohz_full=1-3 rcu_nocb_poll irqaffinity=0
```

### Parámetros en tiempo de ejecución mediante `sysctl`

El comando `sysctl` se utiliza para modificar los parámetros del kernel
en tiempo de ejecución. Los parámetros disponibles son los listados en
`/proc/sys/`. Para el caso de la latencia, el manual de usuario de
LinuxCNC {cite}`linuxcncdoc` sugiere el
siguiente parámetro:

- `sysctl.kernel.sched_rt_runtime_us`: Límite global sobre el tiempo
    máximo de CPU que pueden usar las tareas en tiempo real. Establecer
    a -1 para eliminar el límite de tiempo. Más información sobre este
    parámetro se puede consultar en
    <https://www.kernel.org/doc/html/latest/scheduler/sched-rt-group.html>.

Para establecer estos parámetros de forma persistente se deben añadir al
archivo `/etc/sysctl.conf` o preferiblemente a un nuevo archivo dentro
del directorio `/etc/sysctl.d`. Para más información consultar la página
de manual de `sysctl.conf`.
