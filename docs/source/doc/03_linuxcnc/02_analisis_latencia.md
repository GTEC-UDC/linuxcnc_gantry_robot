# Análisis de la latencia del sistema

Como se comentó en la {numref}`sec:linuxcnc_installation`, LinuxCNC requiere de un sistema operativo de tiempo
real, un tipo de sistema operativo diseñado para controlar dispositivos
y procesos en tiempo real. En contraste con los sistemas operativos
tradicionales, los sistemas operativos de tiempo real están diseñados
para garantizar que las tareas críticas se completen dentro de un límite
de tiempo estricto. Estos sistemas son críticos en aplicaciones donde el
tiempo de respuesta es crucial, como en sistemas de control industrial,
sistemas de navegación de aeronaves, o sistemas de frenado antibloqueo
en automóviles, entre otros.

Existen dos tipos principales de sistemas operativos de tiempo real:

- **Sistemas de Tiempo Real Blandos (Soft Real-Time)**: En estos
    sistemas, las tareas críticas tienen límites de tiempo que
    generalmente se cumplen, pero ocasionalmente se pueden incumplir sin
    consecuencias graves. Estos sistemas priorizan la velocidad y la
    eficiencia, permitiendo cierta flexibilidad en los límites de
    tiempo.
- **Sistemas de Tiempo Real Duros (Hard Real-Time)**: Estos sistemas
    tienen límites de tiempo absolutos y estrictos. Las tareas críticas
    deben completarse dentro de un plazo determinado; de lo contrario,
    podría haber consecuencias catastróficas. Los sistemas de tiempo
    real duros son comunes en aplicaciones donde la seguridad es de suma
    importancia.

En nuestro caso, como se comentó en la
{numref}`sec:linuxcnc_installation`, se usará
el sistema operativo Linux con los parches `PREEMPT_RT` para convertirlo
en un sistema de tiempo real. Este es un sistema de tiempo real blando,
y por lo tanto los intervalos de ejecución de los procesos pueden en
ocasiones ser incumplidos. En este caso el factor crítico que debemos
analizar es la latencia o jitter, es decir, las variaciones temporales
en el intervalo de ejecución de las tareas.

En LinuxCNC, históricamente, una de las formas de control para motores
paso a paso más usadas ha sido la generación software de los pulsos de
paso. En este caso es necesario que la latencia sea muy baja, idealmente
de menos de 20 μs, para poder generar los pulsos con suficiente
frecuencia, de forma que se puedan mover los motores de forma precisa y
consistente a las velocidades requeridas.

En nuestro caso, donde usamos placas MESA para generar las señales de
control de los motores, un intervalo de comunicaciones de 1 ms es
normalmente suficiente, por lo que la latencia no es tan crítica como en
el caso anterior. En este caso, una latencia de máximo de 200 μs puede
ser aceptable.

Antes de poner a funcionar LinuxCNC para controlar máquinas debemos
analizar la latencia máxima del sistema y asegurarnos de que es
adecuado. Para esto, LinuxCNC incorpora las siguientes herramientas:

- **Histograma de latencia**: `latency-histogram`
- **Gráfica de latencia**: `latency-plot`
- **Test de latencia**: `latency-test`

:::{important}
No se debe ejecutar LinuxCNC al usar estas herramientas.
:::

:::{important}
Para obtener la latencia máximo las herramientas más adecuadas son el
histograma de latencia o el test de latencia. Es recomendable llevar a
cabo la prueba durante al menos unos minutos. Durante la ejecución de la
prueba, se debería someter al ordenador a una carga significativa. Por
ejemplo, el manual de usuario de LinuxCNC recomienda mover ventanas por
la pantalla, navegar por la web, copiar archivos grandes en el disco,
reproducir música, y ejecutar programas intensivos como `glxgears` en
OpenGL.
:::

Estas herramientas consideran una configuración con dos hilos:

- Un hilo rápido, llamado "base thread", con un período por defecto
    de 25 μs.
- Un hilo más lento, llamado "servo thread", con un período por
    defecto de 1 ms.

En las siguientes secciones se describen cada una de las herramientas.

## Histograma de latencia

La herramienta `latency-histogram` muestra un histograma de latencia
para los hilos "base thread" y "servo thread". Las opciones
disponibles del comando se muestran en el texto de ayuda de la
herramienta en el {numref}`lst:latency-histogram`. La interfaz gráfica de la herramienta se muestra en la
{numref}`fig:linuxcnc_latency_histogram`.

:::{code-block} text
:name: lst:latency-histogram
:caption: Texto de ayuda de la herramienta latency-histogram.

Usage:
   latency-histogram --help | -?
or
   latency-histogram [Options]

Options:
  --base      nS   (base  thread interval, default:   25000, min:  5000)
  --servo     nS   (servo thread interval, default: 1000000, min: 25000)
  --bbinsize  nS   (base  bin size,  default: 100)
  --sbinsize  nS   (servo bin size, default: 100)
  --bbins     n    (base  bins, default: 200)
  --sbins     n    (servo bins, default: 200)
  --logscale  0|1  (y axis log scale, default: 1)
  --text      note (additional note, default: "")
  --show           (show count of undisplayed bins)
  --nobase         (servo thread only)
  --verbose        (progress and debug)
  --nox            (no gui, display elapsed,min,max,sdev for each thread)

Notes:
  Linuxcnc and Hal should not be running, stop with halrun -U.
  Large number of bins and/or small binsizes will slow updates.
  For single thread, specify --nobase (and options for servo thread).
  Measured latencies outside of the +/- bin range are reported
  with special end bars.  Use --show to show count for
  the off-chart [pos|neg] bin
:::

:::{figure} images/linuxcnc/linuxcnc_latency_plot.png
:name: fig:linuxcnc_latency_plot

Herramienta de gráfica de latencia de LinuxCNC.
:::

## Gráfica de latencia

La herramienta `latency-plot` muestra una gráfica de latencia para los
hilos "base thread" y "servo thread". Las opciones disponibles del
comando se muestran en el texto de ayuda de la herramienta en el
{numref}`lst:latency-plot`. La interfaz gráfica
de la herramienta se muestra en la
{numref}`fig:linuxcnc_latency_plot`.

:::{code-block}
:name: lst:latency-plot
:caption: Texto de ayuda de la herramienta latency-plot.

Usage:
      latency-plot --help | -?      (this)
      latency-plot --hal [Options]

Options:
      --base nS  (base  thread interval, default:   25000)
      --servo nS (servo thread interval, default: 1000000)
      --time mS  (report interval, default: 1000)
      --relative (relative clock time (default))
      --actual   (actual clock time)
:::

:::{figure} images/linuxcnc/linuxcnc_latency_histogram.png
:name: fig:linuxcnc_latency_histogram

Herramienta de histograma de latencia de LinuxCNC.
:::

## Test de latencia

La herramienta `latency-test` ejecuta un test de latencia para los hilos
"base thread" y "servo thread", indicando para cada uno el intervalo
y la latencia máxima. Las opciones disponibles del comando se muestran
en el texto de ayuda de la herramienta en el
{numref}`lst:latency-test`. La interfaz gráfica
de la herramienta se muestra en la
{numref}`fig:linuxcnc_latency_test`.

:::{code-block}
:name: lst:latency-test
:caption: Texto de ayuda de la herramienta latency-test.

Usage:
       latency-test [base-period [servo-period]]
   or:
       latency-test period -      # for single thread
   or:
       latency-test -h | --help   # (this text)

Defaults:     base-period=25000nS servo-period=1000000nS
Equivalently: base-period=25µs servo-period=1ms

Times may be specified with suffix "s", "ms", "us" "µs", or "ns"
Times without a suffix and less than 1000 are taken to be in us;
other times without a suffix are taken to be in ns

The worst-case latency seen in any run of latency-test
is written to the file ~/.latency
:::

:::{figure} images/linuxcnc/linuxcnc_latency_test.png
:name: fig:linuxcnc_latency_test

Herramienta de test de latencia de LinuxCNC.
:::
