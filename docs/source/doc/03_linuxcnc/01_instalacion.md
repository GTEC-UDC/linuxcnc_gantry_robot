(sec:linuxcnc_installation)=
# Instalación

LinuxCNC esta disponible para instalar desde los repositorios oficiales
de las distribuciones Debian y Ubuntu. En el montaje de prueba hemos
instalado Debian 12 con el entorno de escritorio XFCE. Una vez instalado el sistema
operativo, seguimos los siguientes pasos para instalar LinuxCNC:

1. Actualizar el índice de paquetes del sistema ejecutando los
    siguientes comandos:

    ```sh
    sudo apt-get update sudo apt-get dist-upgrade
    ```

2. Instalar LinuxCNC con el siguiente comando:

    ```sh
    sudo apt-get install linuxcnc-uspace linuxcnc-uspace-dev
    ```

    LinuxCNC requiere usar un kernel Linux en tiempo real. Por esto, el
    paquete `linuxcnc-uspace` ya incluye como dependencia el paquete
    `linux-image-amd64`, que proporciona el kernel Linux con los parches
    `PREEMPT_RT` para convertirlo en un sistema de tiempo real.

3. Instalar la herramienta de configuración y diagnostico de las placas
    MESA, `mesaflash`. Ejecutar el siguiente comando:

    ```sh
    sudo apt-get install mesaflash
    ```

4. Reiniciar el sistema. Una vez reiniciado, el sistema deberá estar
    usando el kernel en tiempo real. Para comprobar la versión del
    kernel en uso ejecutamos el siguiente comando:

    ```sh
    uname -v
    ```

    La salida deberá especificar la versión del kernel `PREEMPT_RT`, de
    forma parecida a la siguiente salida:

    ```text
    #1 SMP PREEMPT_RT Fri Oct 6 19:02:35 UTC 2023
    ```

5. Opcionalmente, podemos desinstalar el kernel Linux estándar con el
    siguiente comando:

    ```sh
    sudo apt-get remove linux-image-amd64
    ```

Una vez instalado el paquete de LinuxCNC, tendremos disponible la
entrada `CNC` en el menú de aplicaciones, que contendrá lo siguiente:

- **Documentation**: PDFs de documentación de LinuxCNC, incluyendo el
    manual de usuario y las páginas de manual (man pages).
- **G-code Quick-Reference**: Página de referencia rápida de los
    comandos de G-code.
- **Latency Histogram**: Muestra el histograma de latencias del
    sistema.
- **Latency Test**: Ejecuta un test de latencia, permite obtener la
    latencia o jitter máximo del sistema.
- **LinuxCNC**: Lanzador de LinuxCNC, permite seleccionar la
    configuración de LinuxCNC que se desea ejecutar.
- **Pncconf wizard**: Asistente para generar configuraciones de
    LinuxCNC que usen las placas MESA.
- **Stepconf wizard**: Asistente para generar configuraciones de
    LinuxCNC que usen el puerto paralelo para controlar motores paso a
    paso.
