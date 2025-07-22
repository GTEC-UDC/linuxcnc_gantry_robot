(sec:page_communication)=
# "Communication" Page 

The "Communication" configuration page, shown in {numref}`fig:conf_stepper_4`, allows for the configuration of Ethernet and the controller's bus systems. Below we describe the various options available on this page and their recommended settings.

:::{figure} images/config-stepper/04-communication.png
:name: fig:conf_stepper_4

"Communication" configuration page of the stepper motor controller.
:::

## Ethernet TCP/IP

This section allows for configuring TCP/IP connection parameters: IP address, subnet mask, gateway, and hostname. After setting these parameters, you must click the "Reload" button to apply the changes.

In our testbed setup, these parameters were manually configured to the values shown in {numref}`tab:conf_ethernet`. The controllers were connected to a laptop PC via a switch. The parameters were configured to enable connectivity to the laboratory network, although this connection was not ultimately established.

:::{csv-table} Ethernet configuration parameters.
:name: tab:conf_ethernet
:widths: auto
:header: Parameter,Stepper motor,Brushless motor

IP-Address,  10.68.33.120,       10.68.33.121
Subnet Mask, 255.255.252.0,      255.255.252.0
Gateway,     10.68.32.1,         10.68.32.1
Hostname,    igus-dryve-D1-098a, igus-dryve-D1-098e
:::

## Transmission Protocol

This section allows you to select whether communication with the dryve D1 controller's web server should be via an unencrypted HTTP connection or an encrypted HTTPS connection. For an HTTPS connection, an external certificate can be provided, or a self-signed certificate can be generated.

In our testbed setup, the option to use an unencrypted HTTP connection was selected.

## Bus Systems

The controller is equipped with two bus systems, CANopen and Modbus, which enable communication with the controller and control of motor movement. In our case, we will not use either of these systems, as we will control the motor using the inputs and outputs of connectors X2 (digital inputs), X3 (digital outputs), and X4 (analog inputs). Therefore, the "CANopen" and "Modbus TCP Gateway" options have been left at their default setting of "OFF."
