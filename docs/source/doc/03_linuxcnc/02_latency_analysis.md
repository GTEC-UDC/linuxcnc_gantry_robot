# System Latency Analysis

As mentioned in {numref}`sec:linuxcnc_installation`, LinuxCNC requires a real-time operating system (RTOS), a type of operating system designed for real-time device and process control. Unlike traditional operating systems, RTOSs are engineered to ensure that critical tasks are completed within strict time limits. These systems are needed in applications where response time is vital, such as industrial control systems, aircraft navigation systems, and automotive anti-lock braking systems, among others.

There are two primary types of real-time operating systems:

- **Soft Real-Time Systems**: In these systems, critical tasks generally meet their deadlines, but occasional missed deadlines do not lead to severe consequences. These systems prioritize speed and efficiency, allowing some flexibility in timing.
- **Hard Real-Time Systems**: These systems enforce absolute and strict time limits. Critical tasks must be completed within a precise timeframe; otherwise, catastrophic consequences could occur. Hard real-time systems are common in safety-critical applications.

As noted in {numref}`sec:linuxcnc_installation`, our system uses a Linux operating system with `PREEMPT_RT` patches to add real-time capabilities. This is a soft real-time system, meaning that occasional deviations from the scheduled execution intervals of processes may occur. In this context, the critical factor to analyze is latency, or jitter, which refers to temporal variations in task execution intervals.

Historically, one of the most common methods for controlling stepper motors in LinuxCNC has been the software generation of step pulses. In such cases, very low latency, ideally less than 20 μs, is essential to generate pulses frequently enough for precise and consistent motor movement at the required speeds.

In our setup, where MESA boards are used to generate motor control signals, a communication interval of 1 ms is typically sufficient, making latency less critical than in the previous scenario. Here, a maximum latency of 200 μs can be acceptable.

Before running LinuxCNC to control machinery, we should analyze the maximum system latency and confirm that it is adequate. For this purpose, LinuxCNC includes the following tools:

- **Latency Histogram**: `latency-histogram`
- **Latency Plot**: `latency-plot`
- **Latency Test**: `latency-test`

:::{important}
LinuxCNC must not be running when these tools are in use.
:::

:::{important}
To determine the maximum latency, the latency histogram or latency test are the most suitable tools. It is advisable to perform the test for at least several minutes. During the test, the computer should be subjected to a significant load. For example, the LinuxCNC user manual recommends moving windows across the screen, browsing the web, copying large files to disk, playing music, and running intensive programs like `glxgears` in OpenGL.
:::

These tools consider two threads:

- A fast thread, known as the "base thread," with a default period of 25 μs.
- A slower thread, known as the "servo thread," with a default period of 1 ms.

The following sections describe each of these tools.

## Latency Histogram

The `latency-histogram` tool displays a latency histogram for the "base thread" and "servo thread." The available command options are shown in the tool's help text in {numref}`lst:latency-histogram`. The tool's graphical interface is shown in {numref}`fig:linuxcnc_latency_histogram`.

:::{code-block} text
:name: lst:latency-histogram
:caption: Help text for the latency-histogram tool.

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

LinuxCNC latency plot tool.
:::

## Latency Plot

The `latency-plot` tool displays a latency plot for the "base thread" and "servo thread." The available command options are shown in the tool's help text in {numref}`lst:latency-plot`. The tool's graphical interface is shown in {numref}`fig:linuxcnc_latency_plot`.

:::{code-block}
:name: lst:latency-plot
:caption: Help text for the latency-plot tool.

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

LinuxCNC latency histogram tool.
:::

## Latency Test

The `latency-test` tool runs a latency test for the "base thread" and "servo thread," reporting the interval and maximum latency for each. The available command options are shown in the tool's help text in {numref}`lst:latency-test`. The tool's graphical interface is shown in {numref}`fig:linuxcnc_latency_test`.

:::{code-block}
:name: lst:latency-test
:caption: Help text for the latency-test tool.

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

LinuxCNC latency test tool.
:::
