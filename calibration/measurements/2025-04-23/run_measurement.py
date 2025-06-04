#!/usr/bin/env python3
# Example of LinuxCNC control with Python
# See the LinucCNC user manual, section 13.5 - Python Interface

import sys
import linuxcnc
import time
import sys

from collections.abc import Callable
from typing import Optional

from measurements_utils import snake_move


def set_feed_rate(c: linuxcnc.command, v: float):
    c.mdi(f"F{v}")
    c.wait_complete()


def go_to(
    c: linuxcnc.command,
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
    feed_rate: Optional[float] = None,
    wait_timeout: float = -1,
    callback: Optional[Callable[[], None]] = None,
):
    mdi_str = "G1"

    if x is not None:
        mdi_str += f" X{x}"
    if y is not None:
        mdi_str += f" Y{y}"
    if z is not None:
        mdi_str += f" Z{z}"
    if feed_rate is not None:
        mdi_str += f" F{feed_rate}"

    c.mdi(mdi_str)
    if callback is not None:
        callback()

    while (ret := c.wait_complete(wait_timeout)) == -1:
        if callback is not None:
            callback()

    if ret == linuxcnc.RCS_ERROR:
        print("RCS_ERROR", file=sys.stderr)


def program_robot(
    c: linuxcnc.command,
    s: linuxcnc.stat,
) -> None:

    print("time,x,y,z")

    def write_coordinates():
        s.poll()
        print(",".join(str(x) for x in (time.time(), *s.actual_position[:3])))

    # -------------------------
    # Robot movement parameters
    # -------------------------
    feed_rate = 8000
    # start_xy = (800, 800)
    # end_xy = (4700, 4300)
    start_xy = (300, 300)
    end_xy = (5300-300, 5200-300)
    turns = 4
    z_coords = [-1000 + x for x in range(0, 601, 200)]
    wait_timeout = 1/30

    # -------------------------
    # Robot movement commands
    # -------------------------
    coordinates = snake_move(start_xy, end_xy, turns, "H")[:-1]
    coordinates += snake_move(end_xy, start_xy, turns, "V")

    set_feed_rate(c, feed_rate)
    for z in z_coords:
        go_to(c, z=z, wait_timeout=wait_timeout, callback=write_coordinates)
        for x, y in coordinates:
            go_to(c, x, y, wait_timeout=wait_timeout, callback=write_coordinates)


def main():
    s = linuxcnc.stat()  # connect to the status channel
    c = linuxcnc.command()  # connect to the command channel

    def ok_for_mdi() -> bool:
        s.poll()
        return (
            not s.estop
            and s.enabled
            and (s.homed.count(1) == s.joints)
            and (s.interp_state == linuxcnc.INTERP_IDLE)
        )

    if ok_for_mdi():
        c.mode(linuxcnc.MODE_MDI)
        c.wait_complete()  # wait until mode switch executed
        print("OK, running...", file=sys.stderr)
        try:
            program_robot(c, s)
        except KeyboardInterrupt:
            c.abort()
            sys.exit(1)
    else:
        print(
            "Not OK for running. Check that the robot is homed and idle.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except linuxcnc.error as e:
        print("error: ", e)
        print("is LinuxCNC running?")
        sys.exit(1)
