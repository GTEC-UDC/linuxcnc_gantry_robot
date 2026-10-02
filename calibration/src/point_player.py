from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.figure import SubFigure
from mpl_toolkits.mplot3d import art3d, axes3d
from player import Player, PlayerFrameData


def get_title_str(
    frame_idx: int | None,
    time: float | None,
    speedup: int | None,
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
    trail: (
        tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]
        | None
    )


DEFAULT_POINT_PLOT_STYLE = {
    "color": "r",
    "marker": "o",
    "markersize": 5,
}

DEFAULT_TRAIL_PLOT_STYLE = {
    "color": "b",
    "linestyle": "-",
    "alpha": 0.25,
}


class PointPlayer(Player[PointFrameData]):
    def __init__(
        self,
        ax: axes3d.Axes3D,
        df: pd.DataFrame,
        time_col: str = "time",
        coord_cols: list[str] | None = None,
        point_plot_style: dict[str, Any] | None = None,
        trail_plot_style: dict[str, Any] | None = None,
        trail_after_samples: int | None = None,
        trail_before_samples: int | None = None,
        init_cb: Callable[[], Iterable[Artist]] | None = None,
        update_cb: Callable[[PointFrameData], Iterable[Artist]] | None = None,
        **kwargs,
    ):
        point_plot_style = (
            DEFAULT_POINT_PLOT_STYLE if point_plot_style is None else point_plot_style
        )
        trail_plot_style = (
            DEFAULT_TRAIL_PLOT_STYLE if trail_plot_style is None else trail_plot_style
        )

        self.ax = ax
        self.df = df
        self.time_col = time_col
        self.coord_cols = coord_cols or ["x", "y", "z"]
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

        if isinstance(ax.figure, SubFigure):
            raise ValueError("The player cannot be created in a subfigure")

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
            trail_before_samples = self.trail_before_samples or 0
            trail_after_samples = self.trail_after_samples or 0

            trail_min = max(0, frame_idx - trail_before_samples)
            trail_max = min(len(self.df), frame_idx + trail_after_samples)

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

    def set_title(self, frame_data: PointFrameData | None = None) -> Artist:
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

        if self.trail and frame_data.trail:
            self.trail.set_data_3d(
                frame_data.trail[0], frame_data.trail[1], frame_data.trail[2]
            )
            ret.append(self.trail)

        if self.update_cb:
            ret.extend(self.update_cb(frame_data))

        return ret
