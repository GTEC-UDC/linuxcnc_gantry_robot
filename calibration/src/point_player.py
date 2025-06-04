from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import Any, Optional, cast

import pandas as pd
import mpl_toolkits.mplot3d.art3d as art3d
import mpl_toolkits.mplot3d.axes3d as axes3d
import numpy as np
import numpy.typing as npt
from matplotlib.artist import Artist

from player import Player, PlayerFrameData


def get_title_str(
    frame_idx: Optional[int],
    time: Optional[float],
    speedup: Optional[int],
    paused: bool,
) -> str:
    title_str = "Gantry Movement Animation -- "

    if time:
        title_str += f"{time:.2f} s "

    if frame_idx:
        title_str += f"[{frame_idx}] "

    if speedup:
        title_str += f"({speedup}x) "

    if paused:
        title_str += "(Paused)"

    return title_str.strip()


@dataclass
class PointFrameData(PlayerFrameData):
    pos: tuple[float, float, float]
    trail: Optional[
        tuple[
            npt.NDArray[np.float64],
            npt.NDArray[np.float64],
            npt.NDArray[np.float64],
        ]
    ]


class PointPlayer(Player):
    def __init__(
        self,
        ax: axes3d.Axes3D,
        df: pd.DataFrame,
        time_col: str = "time",
        coord_cols: list[str] = ["x", "y", "z"],
        point_plot_style: dict[str, Any] = {"color": "r", "marker": "o", "markersize": 5},
        trail_plot_style: dict[str, Any] = {"color": "b", "linestyle": "-", "alpha": 0.25},
        trail_after_samples: Optional[int] = None,
        trail_before_samples: Optional[int] = None,
        init_cb: Optional[Callable[[], Iterable[Artist]]] = None,
        update_cb: Optional[Callable[[PointFrameData], Iterable[Artist]]] = None,
        **kwargs,
    ):
        self.ax = ax
        self.df = df
        self.time_col = time_col
        self.coord_cols = coord_cols
        self.trail_after_samples = trail_after_samples
        self.trail_before_samples = trail_before_samples
        self.init_cb = init_cb
        self.update_cb = update_cb


        # Initialize the trail
        if trail_after_samples or trail_before_samples:
            self.trail = cast(
                art3d.Line3D,
                ax.plot([], [], [], **trail_plot_style)[0],
            )
        else:
            self.trail = None

        # Initialize the point
        self.point = cast(
            art3d.Line3D,
            ax.plot([], [], [], **point_plot_style)[0],
        )

        # Initialize the parent
        super().__init__(ax.figure, **kwargs)


    def get_start_frame_idx(self) -> int:
        return 0

    def get_end_frame_idx(self) -> int:
        return len(self.df) - 1

    def get_start_frame_time(self) -> float:
        return self.df[self.time_col].iloc[0].item()

    def get_end_frame_time(self) -> float:
        return self.df[self.time_col].iloc[-1].item()

    def get_frame_time(self, frame_idx: int) -> float:
        return self.df[self.time_col].iloc[frame_idx].item()

    def get_frame_data(self, frame_idx: int) -> PointFrameData:
        x = self.df[self.coord_cols[0]][frame_idx].item()
        y = self.df[self.coord_cols[1]][frame_idx].item()
        z = self.df[self.coord_cols[2]][frame_idx].item()

        if self.trail is not None:
            trail_min = max(0, (frame_idx - self.trail_before_samples))
            trail_max = min(len(self.df), (frame_idx + self.trail_after_samples))

            trail_x = self.df[self.coord_cols[0]][trail_min:trail_max].to_numpy()
            trail_y = self.df[self.coord_cols[1]][trail_min:trail_max].to_numpy()
            trail_z = self.df[self.coord_cols[2]][trail_min:trail_max].to_numpy()

            trail = (trail_x, trail_y, trail_z)
        else:
            trail = None

        return PointFrameData(
            frame_idx,
            self.get_frame_time(frame_idx),
            (x, y, z),
            trail,
        )

    def set_title(self, frame_data: Optional[PointFrameData] = None) -> Artist:
        frame_time = frame_data.frame_time if frame_data else None
        frame_idx = frame_data.frame_idx if frame_data else None
        title_str = get_title_str(frame_idx, frame_time, self.play_speed, not self.run)
        title = self.ax.set_title(title_str)

        return title

    def init(self):
        title = self.set_title()
        self.point.set_data_3d([], [], [])
        ret = [self.point, title]

        if self.trail:
            self.trail.set_data_3d([], [], [])
            ret.append(self.trail)

        if self.init_cb:
            ret.extend(self.init_cb())

        return ret

    def update(self, frame_data: PointFrameData | None):
        title = self.set_title(frame_data)

        if frame_data is None:
            return [title]

        self.point.set_data_3d(
            [frame_data.pos[0]], [frame_data.pos[1]], [frame_data.pos[2]]
        )
        ret = [self.point, title]

        if self.trail:
            self.trail.set_data_3d(
                frame_data.trail[0], frame_data.trail[1], frame_data.trail[2]
            )
            ret.append(self.trail)

        if self.update_cb:
            ret.extend(self.update_cb(frame_data))

        return ret
