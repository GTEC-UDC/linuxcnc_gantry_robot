(sec:linuxcnc_installation)=
# Installation

LinuxCNC is available for installation from the official repositories of Debian and Ubuntu distributions. For our testbed setup, we installed Debian 12 with the XFCE desktop environment. Once the operating system is installed, follow these steps to install LinuxCNC:

1. Update the system's package index by running the following commands:

    ```sh
    sudo apt-get update sudo apt-get dist-upgrade
    ```

2. Install LinuxCNC using the following command:

    ```sh
    sudo apt-get install linuxcnc-uspace linuxcnc-uspace-dev
    ```

    LinuxCNC requires a real-time Linux kernel. The `linuxcnc-uspace` package includes `linux-image-amd64` as a dependency, which provides the Linux kernel with `PREEMPT_RT` patches to convert it into a real-time system.

3. Install `mesaflash`, the MESA board configuration and diagnostic tool, using the following command:

    ```sh
    sudo apt-get install mesaflash
    ```

4. Restart the system. After restarting, the system should be using the real-time kernel. To verify the kernel version in use, run the following command:

    ```sh
    uname -v
    ```

    The output should specify the `PREEMPT_RT` kernel version, similar to the example below:

    ```text
    #1 SMP PREEMPT_RT Fri Oct 6 19:02:35 UTC 2023
    ```

5. Optionally, you can uninstall the standard Linux kernel with the following command:

    ```sh
    sudo apt-get remove linux-image-amd64
    ```

Once the LinuxCNC package is installed, a "CNC" entry will appear in the applications menu, which will contain the following items:

- **Documentation**: LinuxCNC documentation in PDF format, including the user manual and man pages.
- **G-code Quick-Reference**: A quick reference page for G-code commands.
- **Latency Histogram**: Display a latency histogram.
- **Latency Test**: Run a latency test to determine the maximum system latency or jitter.
- **LinuxCNC**: The LinuxCNC launcher, allowing you to select the LinuxCNC configuration to execute.
- **Pncconf wizard**: A wizard for generating LinuxCNC configurations that use MESA boards.
- **Stepconf wizard**: A wizard for generating LinuxCNC configurations that use the parallel port to control stepper motors.
