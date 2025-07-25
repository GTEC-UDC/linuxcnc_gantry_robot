# System Latency Tuning

The maximum system latency can depend on various factors such as hardware, firmware configuration, system load, and hardware interrupt handling. If the maximum system latency is too high, adjustments to the system configuration will be necessary to reduce it. Various sources, including official documentation, guides, and talks, provide detailed guidelines for optimizing the performance of real-time Linux systems {cite}`redhat_rt_low_latency,ubuntu_rt_tuning,lfoss2022tips,elc2023preparing`. The LinuxCNC user manual {cite}`linuxcncdoc` also suggests several potential adjustments to reduce latency, which are detailed in {numref}`sec:firmware_settings` and {numref}`sec:linux_settings`.

For our gantry robot setup, we used a Beelink EQR6 mini computer equipped with an AMD Ryzen 5 6600U CPU. In our case, latency values were sufficiently low, similar to the ones shown in {numref}`fig:linuxcnc_latency_plot`, {numref}`fig:linuxcnc_latency_test`, and {numref}`fig:linuxcnc_latency_histogram`. However, note that for other hardware, even with the same operating system, the latency values could be higher. If the system latency becomes too high during LinuxCNC operation, a warning similar to {numref}`fig:linuxcnc_gui_axis_delay_warning` would appear. In that case check {numref}`sec:firmware_settings` and {numref}`sec:linux_settings` for potential solutions.

:::{figure} images/linuxcnc/linuxcnc_gui_axis_delay_warning.png
:name: fig:linuxcnc_gui_axis_delay_warning

LinuxCNC warning for unexpected latency values.
:::

While our system latency measurements were within acceptable ranges, we encountered a high network latency problem on the LinuxCNC communication with the MESA 7I96S via Ethernet. This issue was resolved by replacing the open-source Realtek driver with the official closed-source Realtek driver as explained in {numref}`sec:network_latency_issues`.

(sec:firmware_settings)=

## Firmware Settings

System firmware such as the {{BIOS}} or {{UEFI}}, can significantly impact system latency. This impact varies depending on the hardware manufacturer and the quality of the provided firmware. Firmware is responsible for initializing and configuring system hardware before the operating system loads. If the firmware is not properly configured to provide accurate timing or does not adequately manage interrupts and hardware devices, it can contribute to increased system latency.

The firmware settings recommended in the LinuxCNC user manual {cite}`linuxcncdoc` that can help reduce latency include the following:

- Disable {{APM}}, {{ACPI}}, and other power-saving functions, including all suspension related features and CPU frequency scaling.
- Disable CPU "turbo" mode.
- Disable CPU simultaneous multithreading technology, e.g., Intel's Hyper-Threading technology.
- Disable or limit SMIs (System Management Interrupts).
- Disable unused hardware.

(sec:linux_settings)=

## Linux Settings

Linux offers various options that can help improve latency. Specifically, for our case, we will consider kernel boot command-line parameters and runtime parameters configured via the `sysctl` command. These parameters are described below.

### Kernel Boot Command-Line Parameters

A comprehensive list of parameters is available at <https://docs.kernel.org/admin-guide/kernel-parameters.html>. In Debian, command-line parameters can be specified in the following ways:

1. In the GRUB bootloader, you can press a key (often {kbd}`e`) to edit the selected boot entry and append the parameters to the end of the line. Once added, you can boot the system by pressing {kbd}`F10` or {kbd}`Ctrl+X`.
2. To persistently specify parameters, edit the `/etc/default/grub` file, adding the parameters to the `GRUB_CMDLINE_LINUX_DEFAULT` variable, and then run the `update-grub` command. For more information about GRUB configuration variables, refer to the corresponding manual page at <https://www.gnu.org/software/grub/manual/grub/html_node/Simple-configuration.html>.

For latency optimization, the most relevant parameters, as suggested in the LinuxCNC user manual {cite}`linuxcncdoc`, are:

- `isolcpus`: A list of CPUs that will be isolated from balancing and scheduling algorithms. This prevents most system processes from using the specified CPUs, thereby making more CPU time available for LinuxCNC.
- `irqaffinity`: A list of CPUs to set as the default IRQ affinity mask. This selects the CPUs that will handle interrupts, ensuring that the remaining CPUs do not have to perform this task.
- `rcu_nocbs`: A list of CPUs whose {{RCU}} callbacks will be executed on other CPUs.{cite}`enwiki:1169786538,redhat_rt_rcu`.
- `rcu_nocb_poll`: This option periodically wakes up {{RCU}} callback execution threads using a timer to check for callbacks to execute. Without this option, the CPUs specified in `rcu_nocbs` are responsible for waking up the threads that execute {{RCU}} callbacks {cite}`redhat_rt_rcu`. This option improves the real-time responsiveness of the CPUs listed in `rcu_nocbs` by freeing them from the need to wake up their corresponding threads.
- `nohz_full`: A list of CPUs that will cease receiving timing ticks when only one task is executing. As a result, these CPUs can dedicate more time to executing applications and less time to handling interrupts and context switching. The CPUs in this list will have their {{RCU}} callbacks transferred to other CPUs, as if they had been specified with the `rcu_nocbs` option.

To determine the number of processors in your system, you can use either the `nproc` command or `cat /proc/cpuinfo`. For instance, in a system with 4 CPUs, if you wish to isolate 3 CPUs from disturbances, you can use the following parameters:

```text
isolcpus=1-3 nohz_full=1-3 rcu_nocb_poll irqaffinity=0
```

### Runtime Parameters using `sysctl`

The `sysctl` command is used to modify kernel parameters at runtime. The available parameters are those listed in `/proc/sys/`. For latency, the LinuxCNC user manual {cite}`linuxcncdoc` suggests the following parameter:

- `sysctl.kernel.sched_rt_runtime_us`: This sets a global limit on the maximum CPU time that real-time tasks can consume. Set to -1 to remove the time limit. More information about this parameter can be found at <https://www.kernel.org/doc/html/latest/scheduler/sched-rt-group.html>.

To persistently set these parameters, they must be added to the `/etc/sysctl.conf` file or, preferably, to a new file within the `/etc/sysctl.d` directory. For more information, consult the `sysctl.conf` manual page.

(sec:network_latency_issues)=

## Network Latency Issues

LinuxCNC requires very low latencies for proper operation. In our system, we encountered a specific issue where LinuxCNC would raise the error **"error finishing read"** due to high latencies of network packets when communicating with the MESA 7I96S Ethernet card.

The issue has been documented in the LinuxCNC GitHub repository (<https://github.com/LinuxCNC/linuxcnc/issues/2281>) and seems to affect systems with Realtek network cards more frequently than those with Intel NICs, likely due to the Realtek cards being slower than Intel NICs. Our system has a RealTek 8168h network card and was using the open-source Linux driver `r8168-dkms`.

The problem occurs when excessive latency on the Linux kernel leaves insufficient time for the real-time thread to communicate with the MESA card during a servo thread cycle. When this happens, the MESA card shuts down and operation is disabled until a LinuxCNC restart.

### Solution

The most effective solution we found was to replace the default open-source Realtek driver with the official closed-source Realtek driver. Debian provides three Realtek drivers:

- **r8169**: The default open-source driver included in the Linux kernel.
- **r8168-dkms**: Closed-source driver for a large range of NICs (including our RealTek 8168h).
- **r8125-dkms**: Closed-source driver for 2.5 Gb NICs found on newer PCs.

The r8168-dkms and r8125-dkms drivers are closed-source and available in the non-free archive area of the Debian repositories. For our system with a RealTek 8168h network card, we needed to install the r8168-dkms driver.

To install the correct driver:

1. Enable non-free packages by editing the apt sources list:

   ```bash
   sudo nano /etc/apt/sources.list
   ```

   Add `non-free` to the end of the main repository lines. For example:

   ```text
   deb http://deb.debian.org/debian bookworm main contrib non-free
   deb-src http://deb.debian.org/debian bookworm main contrib non-free
   ```

2. Update the package list:

   ```bash
   sudo apt update
   ```

3. Install the r8168-dkms driver:

   ```bash
   sudo apt install r8168-dkms
   ```

4. Reboot the system to ensure the new driver is loaded:

   ```bash
   sudo reboot
   ```

5. After reboot, verify that the correct driver is loaded:

   ```bash
   sudo ethtool -i <interface_name>
   ```

   The output should show `driver: r8168` instead of `driver: r8169`.

This solution has been reported to work for multiple users experiencing similar issues, and it provides a more stable and lower-latency network connection for LinuxCNC operations.