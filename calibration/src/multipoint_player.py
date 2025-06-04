from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Optional, cast

import mpl_toolkits.mplot3d.art3d as art3d
import mpl_toolkits.mplot3d.axes3d as axes3d
import numpy as np
import numpy.typing as npt
import pandas as pd
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


POS_TYPE = tuple[float, float, float]
POINTS_SEQ_TYPE = tuple[
    npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]
]


@dataclass
class MultiPointFrameData(PlayerFrameData):
    points: list[POS_TYPE]
    markers: list[POINTS_SEQ_TYPE]
    trails: list[POINTS_SEQ_TYPE]


class MultiPointPlayer(Player):
    def __init__(
        self,
        ax: axes3d.Axes3D,
        df: pd.DataFrame,
        time_col: str = "time",
        point_cols: list[tuple[str, str, str]] = [("x", "y", "z")],
        points_styles: list[dict[str, Any]] = [{"color": "r", "marker": "o", "markersize": 5}],
        marker_cols: list[list[tuple[str, str, str]]] = [],
        marker_styles: list[dict[str, Any]] = [],
        trail_cols: list[tuple[str, str, str]] = [("x", "y", "z")],
        trail_styles: list[dict[str, Any]] = [{"color": "b", "linestyle": "-", "alpha": 0.25}],
        trail_after_samples: list[int] | int = [],
        trail_before_samples: list[int] | int = [],
        xlim: Optional[tuple[float, float]] = None,
        ylim: Optional[tuple[float, float]] = None,
        zlim: Optional[tuple[float, float]] = None,
        init_cb: Optional[Callable[[], Iterable[Artist]]] = None,
        update_cb: Optional[Callable[[MultiPointFrameData], Iterable[Artist]]] = None,
        **kwargs,
    ):
        self.ax = ax
        self.df = df
        self.time_col = time_col
        self.point_cols = point_cols
        self.points_styles = points_styles
        self.marker_cols = marker_cols
        self.marker_styles = marker_styles
        self.trail_cols = trail_cols
        self.trail_styles = trail_styles
        self.init_cb = init_cb
        self.update_cb = update_cb

        self.trail_after_samples = (
            trail_after_samples
            if isinstance(trail_after_samples, list)
            else [trail_after_samples] * len(self.trail_cols)
        )

        self.trail_before_samples = (
            trail_before_samples
            if isinstance(trail_before_samples, list)
            else [trail_before_samples] * len(self.trail_cols)
        )

        # Check that number of styles and cols match
        if len(self.points_styles) != len(self.point_cols):
            raise ValueError(
                "Number of point styles must match number of point columns"
            )

        if len(self.marker_styles) != len(self.marker_cols):
            raise ValueError(
                "Number of marker styles must match number of marker columns"
            )

        if len(self.trail_styles) != len(self.trail_cols):
            raise ValueError(
                "Number of trail styles must match number of trail columns"
            )

        # Initialize the points
        self.points = []
        for point_style in self.points_styles:
            self.points.append(
                cast(art3d.Line3D, ax.plot([], [], [], **point_style)[0])
            )

        # Initialize the markers
        self.markers = []
        for marker_style in self.marker_styles:
            self.markers.append(
                cast(art3d.Line3D, ax.plot([], [], [], **marker_style)[0])
            )

        # Initialize the trails
        self.trails = []
        for trail_style in self.trail_styles:
            self.trails.append(
                cast(art3d.Line3D, ax.plot([], [], [], **trail_style)[0])
            )

        # Set axis limits
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_zlim(zlim)

        # Set axis labels
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

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

    def get_frame_data(self, frame_idx: int) -> MultiPointFrameData:
        points = [
            tuple(self.df[c][frame_idx].item() for c in point_col)
            for point_col in self.point_cols
        ]

        trails = []
        for i, trail_cols in enumerate(self.trail_cols):
            trail_min = max(0, (frame_idx - self.trail_before_samples[i]))
            trail_max = min(len(self.df), (frame_idx + self.trail_after_samples[i]))

            trails.append(
                tuple(self.df[c][trail_min:trail_max].to_numpy() for c in trail_cols)
            )

        markers = []
        for i, marker_cols in enumerate(self.marker_cols):
            markers.append(
                tuple(
                    np.array([self.df[p[i]][frame_idx].item() for p in marker_cols])
                    for i in range(3)
                )
            )

        return MultiPointFrameData(
            frame_idx,
            self.get_frame_time(frame_idx),
            points,
            markers,
            trails,
        )

    def set_title(self, frame_data: Optional[MultiPointFrameData] = None) -> Artist:
        frame_time = frame_data.frame_time if frame_data else None
        frame_idx = frame_data.frame_idx if frame_data else None
        title_str = get_title_str(frame_idx, frame_time, self.play_speed, not self.run)
        title = self.ax.set_title(title_str)

        return title

    def init(self):
        title = self.set_title()
        ret = [title]

        for point in self.points:
            point.set_data_3d([], [], [])
            ret.append(point)

        for marker in self.markers:
            marker.set_data_3d([], [], [])
            ret.append(marker)

        for trail in self.trails:
            trail.set_data_3d([], [], [])
            ret.append(trail)

        if self.init_cb:
            ret.extend(self.init_cb())

        return ret

    def update(self, frame_data: MultiPointFrameData | None):
        title = self.set_title(frame_data)
        ret = [title]

        if frame_data is None:
            return ret

        for i, point in enumerate(self.points):
            point.set_data_3d(
                [frame_data.points[i][0]],
                [frame_data.points[i][1]],
                [frame_data.points[i][2]],
            )
            ret.append(point)

        for i, marker in enumerate(self.markers):
            marker.set_data_3d(
                frame_data.markers[i][0],
                frame_data.markers[i][1],
                frame_data.markers[i][2],
            )
            ret.append(marker)

        for i, trail in enumerate(self.trails):
            trail.set_data_3d(
                frame_data.trails[i][0],
                frame_data.trails[i][1],
                frame_data.trails[i][2],
            )
            ret.append(trail)

        if self.update_cb:
            ret.extend(self.update_cb(frame_data))

        return ret
