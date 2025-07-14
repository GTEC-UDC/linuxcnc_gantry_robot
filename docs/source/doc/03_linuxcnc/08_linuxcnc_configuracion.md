(sec:linuxcnc_configuration)=
# Configuración de LinuxCNC

Como se comentó en la {numref}`sec:linuxcnc_intro_config`, una configuración de LinuxCNC se compone de varios
archivos, siendo necesarios por lo menos un archivo INI y un archivo
HAL. En las siguientes secciones se explica la configuración de ambos
tipos de archivo, usando como ejemplo la configuración de prueba
`mesa_7i96s_7i77_xy`.

(sec:linuxcnc_configuration_ini)=
## Configuración INI

### Formato de archivo de configuración .ini

Un archivo `.ini` es un archivo de texto plano que se utiliza para
configurar aplicaciones y programas. Tiene una estructura sencilla que
consiste en secciones y claves con sus respectivos valores. A
continuación, se describe la sintaxis básica de un archivo `.ini`:

- **Secciones**: Las secciones se utilizan para organizar las claves y
    valores. Cada sección comienza con el nombre de sección entre
    corchetes, seguido de cero o más pares clave-valor que pertenecen a
    esa sección. La sintaxis para una sección es la siguiente:

    ```ini
    [nombre_de_seccion]
    ```

- **Claves y Valores**: Dentro de cada sección se pueden definir
    claves y sus valores correspondientes. Las claves son
    identificadores que se utilizan para acceder a los valores
    asociados. La sintaxis para una clave y su valor es la siguiente:

    ```ini
    clave = valor
    ```

    Las claves pueden contener letras y guiones bajos (\_). Los valores
    pueden ser cadenas de texto, números enteros o números de punto
    flotante.

- **Comentarios**: Los comentarios comienzan con el símbolo de punto y
    coma (;) o el símbolo de almohadilla (#). Por ejemplo:

    ```ini
    ; Esto es un comentario
    # Esto también es un comentario
    ```

### Ejemplo: archivo de configuración `mesa_7i96s_7i77_xy.ini`

A continuación se muestran las distintas secciones del archivo de
configuración `mesa_7i96s_7i77_xy.ini`, donde los distintos parámetros
de cada sección aparecen comentados explicando para que sirven. En
algunas secciones no se han especificado todos los parámetros
disponibles, para ver la lista completa de parámetros y su documentación
consultar el manual de usuario de LinuxCNC
{cite}`linuxcncdoc`.

- **Sección EMC**: Configuración general

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 1-12
    :lineno-match:
    :::

- **Sección DISPLAY**: Configuración de la interfaz de usuario. Las
    opciones disponibles pueden depender de la interfaz de usuario que
    se use. En este caso usamos la interfaz de usuario AXIS.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 15-65
    :lineno-match:
    :::

- **Sección TASK**: Configuración del controlador de tareas de
    LinuxCNC. El controlador de tareas se encarga de comunicarse con la
    interfaz de usuario, comunicarse con el planificador de movimiento,
    y comunicarse con el interprete de G-code. Actualmente solo existe
    un controlador de tareas, `milltask`. Para más información consultar
    el manual de usuario de LinuxCNC {cite}`linuxcncdoc` y la página de manual de `milltask`, también disponible
    en <http://linuxcnc.org/docs/devel/html/man/man1/milltask.1.html>.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 68-75
    :lineno-match:
    :::

- **Sección RS274NGC**: Configuración del intérprete RS274NGC
    (G-code).

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 78-85
    :lineno-match:
    :::

- **Sección EMCMOT**: Configuración del controlador de movimiento. Los
    parámetros `EMCMOT` y `SERVO_PERIOD` no son utilizados por LinuxCNC
    directamente, sino que se usan para configurar el módulo de control
    de movimiento en el fichero HAL (ver la
    {numref}`sec:linuxcnc_configuration_hal`).

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 88-101
    :lineno-match:
    :::

- **Sección HAL**: Configuración de HAL.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 104-118
    :lineno-match:
    :::

- **Sección HALUI**: Configuración de HALUI (interfaz de usuario
    basada en HAL). La única opción disponible es `MDI_COMMAND`, que
    permite ejecutar comandos MDI mediante señales de HAL. En nuestro
    caso dejamos la sección vacía.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 121-127
    :lineno-match:
    :::

- **Sección KINS**: Configuración de cinemática.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 130-138
    :lineno-match:
    :::

- **Sección APPLICATIONS**: LinuxCNC permite lanzar aplicaciones al
    iniciarse. Estas deben indicarse dentro de la sección `APPLICATIONS`
    con la opción `APP`, la cual puede especificarse varias veces. Las
    aplicaciones se lanzarán al comienzo antes de que se inicie la
    interfaz gráfica o tras esperar el retardo especificado en la opción
    `DELAY`.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 141-145
    :lineno-match:
    :::

- **Sección TRAJ**: Configuración del planificador de trayectorias.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 148-165
    :lineno-match:
    :::

- **Sección EMCIO**: Configuración del controlador de entrada/salida.
    Este controla tareas de entrada/salida como el refrigerante, el
    cambio de herramientas, y la parada de emergencia.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 168-175
    :lineno-match:
    :::

- **Sección AXIS\_\<e\>**: Configuración del eje *\<e\>*. Los valores
    posibles de *\<e\>* son `X`, `Y`, `Z`, `A`, `B`, `C`, `U`, `V`, y
    `W`. A continuación se muestra como ejemplo la configuración del
    eje X. La configuración del eje Y es similar.

    :::{important}
    En la configuración de los límites del robot (parámetros `MIN_LIMIT`
    y `MAX_LIMIT`) es recomendable dejar algo de margen respecto al
    espacio de trabajo deseado. Si le indicamos al robot que se
    posicione en uno de los límites, es muy fácil que el robot se salga
    mínimamente de ese límite simplemente por vibraciones del motor. Por
    ejemplo, si queremos que nuestro robot trabaje en el eje X entre X =
    0 y X = 200 podemos configurar `MIN_LIMIT = -5` y `MAX_LIMIT = 205`.
    :::

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 178-191
    :lineno-match:
    :::

- **Sección JOINT\_\<n\>**: Configuración de la articulación (motor)
    *\<n\>*, siendo *\<n\>* el número de la articulación, desde 0 hasta
    (*\<num_joints\>* $-$ 1). El valor de *\<num_joints\>* se establece
    en la opción JOINTS de la sección KINS.

    Para máquinas con geometrías cartesianas como robots grúa LinuxCNC
    incluye el modulo de cinemática `trivkins`. Con este modulo por
    defecto hay una correspondencia 1:1 entre la letra de coordenada de
    eje y el número de articulación, i.e., JOINT_0 = X, JOINT_1 = Y,
    ..., JOINT_8 = W.

    El modulo `trivkins` acepta el parámetro `coordinates` para
    especificar la asociación de letras de coordenadas de eje con el
    número de articulación. Por ejemplo, con el parámetro
    `coordinates=XZ` se asignará JOINT_0 = X y JOINT_1 = Z. En este
    parámetro una misma letra de eje se puede especificar varias veces,
    lo que permite asignar varias articulaciones a un mismo eje. En este
    caso es necesario usar también el parámetro `kinstype=B`. Por
    ejemplo, con los parámetros `coordinates=XZ` y `kinstype=B` se
    asignará JOINT_0 = X y JOINT_1 = X.

    Para más información sobre el módulo de cinemática `trivkins`,
    consultar la página del manual `kins`, también disponible en
    <http://linuxcnc.org/docs/devel/html/man/man9/kins.9.html>.

    :::{important}
    Tanto la configuración de articulación como la de eje disponen de
    los parámetros `MAX_VELOCITY`, `MAX_ACCELERATION`, `MIN_LIMIT`, y
    `MAX_LIMIT`. Cuando el robot no está referenciado los parámetros que
    usa LinuxCNC son los de la sección de articulación, pero una vez que
    el robot esta referenciado los parámetros que usa son los de la
    sección de eje.
    :::

    El siguiente código muestra la configuración de la articulación 1
    (eje X), que se corresponde con el motor paso a paso. Los parámetros
    especificados debajo del comentario "Configuraciones personalizadas
    para el archivo HAL" no son usados por LinuxCNC directamente, se
    usan para configurar los parámetros del motor en el fichero HAL (ver
    la {numref}`sec:linuxcnc_configuration_hal`).

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 194-300
    :lineno-match:
    :::

    El siguiente código muestra la configuración de la articulación 2
    (eje Y), que se corresponde con el motor sin escobillas. Igual que
    antes, los parámetros especificados debajo del comentario
    "Configuraciones personalizadas para el archivo HAL" no son usados
    por LinuxCNC directamente, se usan para configurar los parámetros
    del motor en el fichero HAL (ver la
    {numref}`sec:linuxcnc_configuration_hal`).
    Estos parámetros ahora son distintos ya que ha cambiado el tipo de
    motor, antes el motor era paso a paso y ahora es un motor sin
    escobillas.

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.ini
    :language: ini
    :lines: 319-410
    :lineno-match:
    :::

(sec:linuxcnc_configuration_hal)=
## Configuración HAL

La HAL es una parte fundamental de LinuxCNC, que actúa como una interfaz
entre el software y el hardware de la máquina. HAL proporciona la
infraestructura para la comunicación entre los numerosos componentes de
software y hardware del sistema. La capa HAL está compuesta de
componentes que:

- Están conectados entre sí, procesando los datos entrantes y
    proporcionando salidas a otros componentes, e.g., el algoritmo de
    planificación de movimiento informa a los motores de como deben
    moverse.
- Pueden saber cómo comunicarse con el hardware.
- Siempre se ejecutan periódicamente de una de las siguientes formas:
  - Como componentes en tiempo real, bien con una frecuencia de unos
        pocos microsegundos de tiempo de ejecución (e.g., para avanzar
        un motor paso a paso o leer un encoder), o con una frecuencia
        inferior a un milisegundo (e.g., para ajustar la planificación
        de los próximos movimientos para completar una instrucción de
        G-code).
  - Como componentes de espacio de usuario en tiempo no real, que
        pueden interrumpirse o retrasarse si el resto del sistema está
        ocupado o sobrecargado.

Los componentes de HAL incluidos con LinuxCNC se listan en el manual de
usuario {cite}`linuxcncdoc`, también disponible
en <http://linuxcnc.org/docs/stable/html/hal/components.html>. Además,
cada componente dispone de su propia página de manual.

### Conceptos básicos

- **Pines y señales**: HAL se basa en los mismos principios que se
    utilizan para diseñar circuitos y sistemas de hardware, y utiliza
    "pines" y "señales" para representar el flujo de datos entre los
    módulos o componentes de HAL. En resumen:

  - Los pines pueden llevar valores booleanos, flotantes, y enteros
        con o sin signo.
  - Los pines tienen una dirección, que puede ser de entrada (IN),
        de salida (OUT), o de entrada/salida (I/O).
  - Una señal identifica a una conexión entre pines.

    La {numref}`fig:hal_circuit_concept`
    ilustra los conceptos de componentes, pines, y señales en HAL. En la
    figura el pin `pin3-out` de `component.0` se conecta con los pines
    `pin3-in` y `pin4-in` de `component.1` (señal `signal-red`), y el
    pin `pin1-out` de `component.1` se conecta con el pin `pin1-in` de
    `component.0` (señal `signal blue`).

    :::{figure} images/linuxcnc/hal_circuit_concept.png
    :name: fig:hal_circuit_concept

    Concepto de HAL --- Conexión como circuitos eléctricos. Fuente: documentación de LinuxCNC :cite:`linuxcncdoc`.
    :::


- **Parámetros**: Los componentes de HAL pueden tener parámetros,
    i.e., ajustes de entrada o salida que no estarán conectados a ningún
    otro componente pero a los que es necesario acceder. Existen dos
    tipos de parámetros:

  - **Parámetros de entrada**: valores que el usuario puede ajustar
        y que permanecen fijos una vez configurados.
  - **Parámetros de salida**: valores que no pueden ser ajustados
        por el usuario, son puntos de prueba que permiten monitorizar
        las señales internas.

- **Funciones**: Cada componente de HAL tiene una o varias funciones
    que deben ejecutarse para hacer lo que se supone que debe hacer el
    componente. Cada función es un bloque de código que realiza una
    acción específica. Para que las funciones se ejecuten se deberán
    añadir a un hilo.

- **Hilos (threads)**: Los hilos permiten ejecutar las funciones de
    los componentes de HAL en intervalos de tiempo específicos. Al crear
    un hilo se especifica el intervalo de tiempo con el que se
    ejecutarán las funciones asignadas. Posteriormente, las funciones de
    los componentes de HAL pueden pueden ser añadidas al hilo para ser
    ejecutadas en orden en el intervalo de tiempo del hilo.

### Interacción con HAL y comandos

HAL no interactúa directamente con el usuario. LinuxCNC proporciona
proporciona diferentes interfaces para configurar o interactuar con HAL:

- Desde ficheros `.hal`.
- Desde la línea de comandos mediante el comando `halcmd`.
- Desde scripts Python.
- Desde programas C/C++.

La configuración o interacción con HAL con cualquiera de estas
interfaces se realiza mediante comandos. La lista completa de comandos
se detalla en la página de manual de `halcmd`, también disponible en
<http://linuxcnc.org/docs/html/man/man1/halcmd.1.html>. Los comandos más
relevantes son los siguientes.

:::{note}
De forma general cada comando debe especificarse en una única línea, si
se quiere dividir un comando en varias líneas puede utilizarse el
carácter de de barra invertida (\\) para indicar que la línea se
prolonga hasta la línea siguiente. La barra invertida debe ser el último
carácter antes de la nueva línea.
:::

- `loadrt`: Carga un componente de tiempo real de HAL en el sistema.
    La sintaxis básica del comando `loadrt` es la siguiente:

    ```text
    loadrt <componente> <opciones>
    ```

    donde `<componente>` es el nombre del componente y `<opciones>` son
    las opciones del componente. Por ejemplo:

    ```hal
    loadrt mux4 count=1
    ```

- `addf`: Añade una función a un hilo de tiempo real. La sintaxis del
    comando `addf` es la siguiente:

    ```text
    addf <función> <hilo>
    ```

    donde `<función>` es el nombre de la función e `<hilo>` es el hilo
    al que se añadirá. Por ejemplo:

    ```hal
    addf mux4.0 servo-thread
    ```

- `loadusr`: Carga un componente de tiempo no real de HAL en el
    sistema. Los componentes que no son en tiempo real son procesos
    separados, que opcionalmente pueden comunicarse con otros
    componentes HAL a través de pines y parámetros. No se pueden cargar
    componentes de tiempo real en el espacio de tiempo no real. La
    sintaxis del comando `loadusr` es la siguiente:

    ```text
    loadusr [<flags>] <commando>
    ```

    donde `<commando>` es el comando del programa que se desea ejecutar
    y `<flags>` puede ser una o más de las siguientes opciones:

  - `-i`: Ignorar el valor de retorno del programa (con `-w`).
  - `-w`: Esperar a que finalice el programa.
  - `-W`: Esperar a que el componente esté listo. Se asume que el
        componente tendrá el mismo nombre que el primer argumento del
        comando.
  - `-Wn``<name>`: Esperar a que el componente esté listo y
        asignarle el nombre `<name>`. Solo es aplicable si el componente
        tiene la opción `-n` para asignar un nombre.

    Por ejemplo:

    ```hal
    loadusr -Wn spindle gs2_vfd -n spindle
    ```

- `net`: Crear una conexión entre una señal y uno o varios pines. La
    sintaxis es la siguiente:

    ```text
    net <señal> <pin>
    ```

    donde `<señal>` es el nombre de la señal y `<pin>` es el nombre de
    un pin. Si la señal no existe se crea la nueva señal. El comando
    permite también usar las palabras `<=`, `=>`, y `<=>`, separadas por
    un espacio de los nombres de los pines, para indicar la dirección de
    las señales entre pines. Estas palabras son ignoradas por el
    comando, simplemente sirven para facilitar la lectura del comando y
    el seguimiento de la lógica.

    Las siguientes reglas deben cumplirse para conectar un pin a una
    señal:

  - Un pin de entrada (IN) siempre puede conectarse a una señal.
  - Un pin de entrada/salida (I/O) puede conectarse a menos que haya
        un pin de salida (OUT) en la señal.
  - Un pin de salida (OUT) puede conectarse solo si no hay otros
        pines de salida (OUT) o de entrada/salida (I/O) en la señal.

    El mismo nombre de señal puede utilizarse en varios comandos `net`
    para conectar pines adicionales, siempre que se respeten las reglas
    anteriores.

    Ejemplos:

    - ```hal
       net home-x joint.0.home-sw-in <= parport.0.pin-11-in
       ```

       donde `home-x` es el nombre de la señal, `joint.0.home-sw-in` es
       un pin de entrada (IN), `<=` es la flecha de dirección opcional
       (ignorada por el comando), y `parport.0.pin-11-in` es un pin de
       salida (OUT).

       Este ejemplo también se puede definir en HAL de forma
       equivalente mediante dos comandos `net`:

       ```hal
       net home-x <= parport.0.pin-11-in
       net home-x => joint-0.home-sw-in
       ```

       :::{note}
       Como se ve en este ejemplo, aunque el nombre del segundo pin
       tiene el sufijo `-in`, HAL lo trata como pin de salida. Por lo
       tanto, al configurar las conexiones de pines en HAL, deberemos
       fijarnos en como está configurado el pin en HAL y no en su
       nombre.
       :::

    - ```hal
      net xStep stepgen.0.out => parport.0.pin-02-out parport.0.pin-08-out
      ```

      donde `xStep` es el nombre de la señal, `stepgen.0.out` es un
      pin de salida, y `parport.0.pin-02-out` y `parport.0.pin-08-out`
      son pines de entrada.

      Este ejemplo también se puede definir en HAL mediante dos
      comandos `net` de la siguiente forma:

      ```hal
      net home-x <= stepgen.0.out
      net home-x => parport.0.pin-02-out parport.0.pin-08-out
      ```

- `setp`: Establece el valor de un pin o parámetro. Los valores
    válidos dependerán del tipo de datos del pin o parámetro. La
    sintaxis de este comando es la siguiente:

    ```text
    setp <nombre> <valor>
    ```

    donde `<nombre>` es el nombre del pin o parámetro y `<valor>` es el
    valor al que se quiere establecer. El comando fallará si `<nombre>`
    no existe como pin o parámetro, si es un parámetro de solo lectura,
    si es un pin de salida (OUT), si es un pin que ya está conectado a
    una señal, o si `<valor>` no es un valor válido para el tipo de
    datos del pin o parámetro.

- `sets`: Establece el valor de una señal. La sintaxis es la
    siguiente:

    ```text
    sets <señal> <valor>
    ```

    donde `<señal>` es el nombre de la señal y `<valor>` es el valor al
    que se quiere establecer. El comando fallará si `<señal>` no existe
    como señal, si la señal ya está conectada a un pin de salida (OUT),
    o si `<valor>` no es un valor válido para el tipo de datos de la
    señal.

- `unlinkp`: Desvincula un pin de la señal conectada. La sintaxis del
    comando es:

    ```hal
    unlinkp <nombre>
    ```

    donde `<nombre>` es el nombre del pin. Si el pin no tiene una señal
    conectada no ocurre nada. El comando fallará si `<nombre>` no existe
    como pin.

### Formato de archivo `.hal`

Un archivo `.hal` es un archivo de texto plano que contiene comandos de
HAL. Se pueden incluir comentarios comenzando con el símbolo de
almohadilla (#). Se puede acceder a las opciones del archivo `.ini` con
la sintaxis `[<sección>]<opción>`, donde `[<sección>]` es el nombre de
la sección entre corchetes y `<opción>` es el nombre de la opción
correspondiente dentro de esa sección.

### Ejemplo: archivo de configuración `mesa_7i96s_7i77_xy.hal`

Como se comentó en la {numref}`sec:linuxcnc_intro_config`, una configuración de LinuxCNC incluye por lo menos un
archivo `.ini` y un archivo `.hal`. A continuación se muestra el archivo
de configuración `mesa_7i96s_7i77_xy.hal`, correspondiente al archivo
`mesa_7i96s_7i77_xy.ini` detallado en la
{numref}`sec:linuxcnc_configuration_ini`. A
diferencia del formato `.ini`, el formato `.hal` no tiene una sintaxis
de secciones, sin embargo, por simplicidad a continuación se muestra el
archivo dividido en diferentes partes.

- **Cargar módulos, añadir funciones a hilos, y otras configuraciones
    iniciales**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 1-54
    :lineno-match:
    :::

- **Configuración del eje X (articulación 0, motor paso a paso)**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 57-120
    :lineno-match:
    :::

- **Configuración del eje Y (articulación 1, motor sin escobillas)**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 123-179
    :lineno-match:
    :::

- **Otras configuraciones**:

    :::{literalinclude} codes/mesa_7i96s_7i77_xy.hal
    :language: hal
    :lines: 182-265
    :lineno-match:
    :::

## Herramientas de HAL

Existen varias herramientas de HAL que permiten la visualización y el
diagnóstico de los estados de los pines en tiempo real. A continuación
se describen las más destacadas, para ver la lista completa de
herramientas consultar el manual de usuario de LinuxCNC
{cite}`linuxcncdoc`.

### Halcmd

`halcmd` es una herramienta de línea de comandos para interactuar con
HAL. Al ejecutar `halcmd` aparecerá la siguiente línea de comando:

```text
halcmd:
```

que nos permitirá introducir y ejecutar comandos HAL. Aparte de los
comandos detallados anteriormente en la
{numref}`sec:linuxcnc_configuration_hal`,
existen otros comandos que pueden ser de gran utilidad como `show`,
`list`, o `save`. Estos comandos permiten imprimir los distintos
elementos definidos en HAL como pines, parámetros, hilos, etc. La lista
completa de comandos se detalla en la página de manual de `halcmd`,
también disponible en
<http://linuxcnc.org/docs/html/man/man1/halcmd.1.html>.

### Halshow

`halshow` es una herramienta gráfica que permite ver y monitorizar los
componentes de HAL como pines, parámetros, señales, y funciones. Esta
herramienta se muestra en las Figuras
{numref}`%s <fig:halshow_show>` y
{numref}`%s <fig:halshow_watch>`. La
herramienta dispone de los siguientes elementos principales:

- Vista de árbol con los pines, parámetros, señales, funciones, etc.,
    de HAL. Esta vista se encuentra a la izquierda de la ventana como se
    puede ver en las Figuras {numref}`%s <fig:halshow_show>` y {numref}`%s <fig:halshow_watch>`.
- Entrada de texto para ejecutar comandos HAL, situada en la parte
    inferior como se muestra en las Figuras
    {numref}`%s <fig:halshow_show>` y
    {numref}`%s <fig:halshow_watch>`.
- Pestaña "SHOW" donde se muestra la información del elemento
    seleccionado en la vista de árbol. Esto se muestra en la
    {numref}`fig:halshow_show`.
- Pestaña "WATCH" en la que podemos monitorizar y establecer valores
    de pines o parámetros de HAL. Podemos añadir elementos aquí haciendo
    clic en ellos en la vista de árbol. Esto se muestra en la
    {numref}`fig:halshow_watch`.
- Pestaña "SETTINGS" con varias opciones como por ejemplo el
    intervalo de refresco o el formato de los parámetros mostrados.

El menú {menuselection}`File` permite guardar
los elementos monitorizados de la pestaña "WATCH" en un archivo, así
como cargar una lista de elementos a monitorizar existente de archivo.

Podemos abrir la herramienta Halshow desde la interfaz gráfica AXIS
haciendo clic en {menuselection}`Machine --> Show Hal Configuration`.

:::{figure} images/linuxcnc/halshow_show.png
:name: fig:halshow_show
:width: 70%

Herramienta Halshow mostrando la pestaña "SHOW".
:::

:::{figure} images/linuxcnc/halshow_watch.png
:name: fig:halshow_watch
:width: 70%

Herramienta Halshow mostrando la pestaña "WATCH".
:::

### Halscope

`halscope` es una herramienta gráfica que proporciona un osciloscopio
para HAL. Permite capturar y mostrar el valor de pines, señales, y
parámetros a lo largo de un intervalo de tiempo. Esta herramienta se
muestra en la {numref}`fig:halscope`. El menú
{menuselection}`File` permite guardar la
configuración actual o abrir una configuración previamente guardada. Al
cerrar `halscope`, la configuración se guarda automáticamente en el
archivo `autosave.halscope`.

:::{figure} images/linuxcnc/hal_oscilloscope.png
:name: fig:halscope

Herramienta Halscope mostrando los valores de los pines `joint.0.motor-pos-cmd` (posición del motor comandada por LinuxCNC) y `joint.0.motor-pos-fb` (posición del motor leída del encoder) a lo largo del tiempo.
:::

Podemos abrir la herramienta Halscope desde la interfaz gráfica AXIS
haciendo clic en {menuselection}`Machine --> Hal scope`.

### Halreport

`halreport` es una herramienta de de línea de comandos que permite
generar un informe sobre las conexiones de HAL. La salida de ayuda del
comando es la siguiente:

```text
Usage:
    halreport -h | --help (this help)
or
    halreport [outfilename]
```

El informe generado muestra todas las conexiones de señales e indica
posibles problemas. La información incluida en el informe, entre otras,
es la siguiente:

- Descripción del sistema y versión del kernel.
- Señales y sus pines de salida, entrada, y entrada/salida conectados.
- Funciones, hilos, y comandos `addf` correspondientes a cada pin.
- Nombres reales para pines que usan alias.
- Señales sin salida.
- Señales sin entradas.
- Funciones no añadidas a hilos.
- Aviso de componentes marcados como obsoletos.

## Programación con lógica de escalera

LinuxCNC incluye el componente ClassicLadder, una implementación libre
de un intérprete de escalera publicado bajo la LGPL.

La lógica de escalera, o el lenguaje de programación de escalera, es un
método para dibujar esquemas lógicos eléctricos. Originalmente concebido
para describir sistemas de control con relés, este enfoque se ha
convertido en un lenguaje gráfico ampliamente utilizado para programar
PLCs. Recibe su nombre del hecho de que los programas en este lenguaje
se asemejan a escaleras, con dos rieles verticales y una serie de
peldaños horizontales entre ellos.

Para usar ClassicLadder debemos cargar el módulo de tiempo real
`classicladder_rt` en HAL y añadir la función `classicladder.0.refresh`
al hilo `servo-thread` mediante los siguientes comandos:

```hal
loadrt classicladder_rt addf classicladder.0.refresh servo-thread
```

Una vez hecho esto podemos abrir la interfaz gráfica de ClassicLadder
con el comando de sistema `classicladder`, o desde la interfaz AXIS
haciendo clic en {menuselection}`File --> Ladder Editor...`. La interfaz gráfica de ClassicLadder nos
permitirá elaborar programas en lógica de escalera, así como ver el
estado lógico de los distintos componentes del programa. Esta interfaz
está compuesta por varias ventanas como se muestra en la
{numref}`fig:classicladder`.

:::{figure} images/linuxcnc/linuxcnc_ladder_editor.png
:name: fig:classicladder

Interfaz gráfica de ClassicLadder.
:::

En el montaje de prueba, se ha usado la lógica de escalera para
programar el funcionamiento del panel de indicadores LED. El programa
creado con ClassicLadder se ha guardado en el archivo `myladder.clp`.
Para usarlo en LinuxCNC se puede cargar con el siguiente comando de HAL:

```hal
loadusr classicladder myladder.clp -nogui
```

El manual de usuario de LinuxCNC {cite}`linuxcncdoc` incluye una guía detallada de ClassicLadder. Una buena
introducción a ClassicLadder es la serie "Classicladder tutorials" de
"The Feral Engineer" en YouTube:
<https://www.youtube.com/playlist?list=PLTYvfbjLClpfAfJSGhZUecgXFwVPY5e09>.
