import math
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator, Iterable
from dataclasses import dataclass
from typing import Optional

from matplotlib.figure import Figure
from matplotlib.artist import Artist
from matplotlib.animation import FuncAnimation


@dataclass
class PlayerFrameData:
    frame_idx: int
    frame_time: float


class Player(FuncAnimation, ABC):
    def __init__(
        self,
        fig: Figure,
        draw_on_pause: bool = True,  # do not stop the event source on pause
        save_count: int = 1000,
        loop: bool = True,
        play_speed: int = 1,
        interval: float = 0,
        real_time: bool = True,
        **kwargs,
    ):
        self.fig = fig
        self.draw_on_pause = draw_on_pause
        self.run = True
        self.play_speed = play_speed
        self.elapsed_time = 0
        self.frame_idx = 0
        self.loop = loop
        self.real_time = real_time

        super().__init__(
            fig,
            self.update,
            frames=self.generate_frames(),
            init_func=self.init,
            save_count=save_count,
            interval=interval,
            **kwargs,
        )

        # Connect keys to control the animation
        self.on_key_cid = self.fig.canvas.mpl_connect("key_press_event", self.on_key)

    @abstractmethod
    def get_start_frame_idx(self) -> int: ...

    @abstractmethod
    def get_end_frame_idx(self) -> int: ...

    @abstractmethod
    def get_start_frame_time(self) -> float: ...

    @abstractmethod
    def get_end_frame_time(self) -> float: ...

    @abstractmethod
    def get_frame_time(self, frame_idx: int) -> float: ...

    @abstractmethod
    def get_frame_data(self, frame_idx: int) -> PlayerFrameData: ...

    def start(self):
        self.run = True
        if not self.draw_on_pause:
            self.event_source.start()

    def stop(self):
        self.run = False
        if not self.draw_on_pause:
            self.event_source.stop()

    def go_to_frame(self, frame_idx: int):
        max_frame, min_frame = self.get_end_frame_idx(), self.get_start_frame_idx()
        self.frame_idx = max(min_frame, min(max_frame, frame_idx))
        self.elapsed_time = self.get_frame_time(self.frame_idx)

    def go_to_start(self):
        self.frame_idx = self.get_start_frame_idx()
        self.elapsed_time = self.get_start_frame_time()

    def go_to_end(self):
        self.frame_idx = self.get_end_frame_idx()
        self.elapsed_time = self.get_end_frame_time()

    def set_play_speed(self, play_speed: int):
        self.play_speed = play_speed
        if play_speed == 0:
            self.stop()
        else:
            self.start()

    def increase_play_speed_integer(
        self, factor: int = 1, include_one: bool = True, skip_zero: bool = True
    ):
        assert factor > 0, "The factor number must be positive"

        if include_one and (self.play_speed == 0 or self.play_speed == -1):
            self.play_speed = 1
        elif include_one and -factor <= self.play_speed < 0:
            self.play_speed = -1
        else:
            self.play_speed = math.floor(self.play_speed / factor) * factor + factor
            if skip_zero and self.play_speed == 0:
                self.increase_play_speed_integer(factor, include_one, skip_zero)

    def decrease_play_speed_integer(
        self, factor: int = 1, include_one: bool = True, skip_zero: bool = True
    ):
        assert factor > 0, "The factor number must be positive"

        if include_one and (self.play_speed == 0 or self.play_speed == 1):
            self.play_speed = -1
        elif include_one and 0 < self.play_speed <= factor:
            self.play_speed = 1
        else:
            self.play_speed = math.ceil(self.play_speed / factor) * factor - factor

        if skip_zero and self.play_speed == 0:
            self.decrease_play_speed_integer(factor, include_one, skip_zero)

    def step(self, num_frames: int = 1):
        self.go_to_frame(self.frame_idx + num_frames)

    def toggle_run(self):
        if self.run:
            self.stop()
        else:
            self.start()

    def get_help_text(self) -> str:
        return """\
Animation Controls:
------------------
Space: Play/Pause
PageUp/PageDown: Increase/Decrease playback speed
Shift + PageUp/PageDown: Increase/Decrease playback speed by 5x
m/n: Step forward/backward 1 frame
M/N: Step forward/backward 60 frames
Ctrl+m/Ctrl+n: Step forward/backward 600 frames
i/o: Jump to start/end
"""

    def on_key(self, event):
        if event.key == "pageup":
            self.increase_play_speed_integer()
            print(f"Play speed: {self.play_speed}")
        elif event.key == "pagedown":
            self.decrease_play_speed_integer()
            print(f"Play speed: {self.play_speed}")
        elif event.key == "shift+pageup":
            self.increase_play_speed_integer(5)
            print(f"Play speed: {self.play_speed}")
        elif event.key == "shift+pagedown":
            self.decrease_play_speed_integer(5)
            print(f"Play speed: {self.play_speed}")
        elif event.key == "n":
            self.step(-1)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "m":
            self.step(1)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "N":
            self.step(-60)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "M":
            self.step(60)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "ctrl+n":
            self.step(-600)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "ctrl+m":
            self.step(600)
            print(f"Frame: {self.frame_idx}")
        elif event.key == "i":
            self.go_to_start()
            print("Go to start")
        elif event.key == "o":
            self.go_to_end()
            print("Go to end")
        elif event.key == " ":
            if self.run:
                self.stop()
                print("Stopped")
            else:
                self.start()
                print("Running")

    # Animation initialization function
    @abstractmethod
    def init(self) -> Iterable[Artist]: ...

    # Animation update function
    @abstractmethod
    def update[
        T: PlayerFrameData
    ](self, frame_data: Optional[T]) -> Iterable[Artist]: ...

    def generate_frames_real_time(self) -> Iterator[Optional[PlayerFrameData]]:
        frame_data: Optional[PlayerFrameData] = None
        last_time = time.time()  # Last update time
        start_time = self.get_start_frame_time()
        end_time = self.get_end_frame_time()

        # set frame_idx and elapsed_time to the start of the video
        self.go_to_start()

        while self.run or self.draw_on_pause:
            current_time = time.time()
            dt = current_time - last_time  # Time delta
            last_time = current_time

            if not self.run or self.play_speed == 0:
                # The frame index may change when the animation is paused
                if not frame_data or frame_data.frame_idx != self.frame_idx:
                    frame_data = self.get_frame_data(self.frame_idx)
                yield frame_data
                continue

            # Accumulate playback time using current speedup
            self.elapsed_time += dt * self.play_speed

            # Update frame_idx to match elapsed_playback_time
            if self.play_speed > 0:
                if self.loop and self.elapsed_time > end_time:
                    self.go_to_start()

                while (self.get_frame_time(self.frame_idx)) < self.elapsed_time:
                    self.frame_idx += 1
            else:
                if self.loop and self.elapsed_time < start_time:
                    self.go_to_end()

                while (self.get_frame_time(self.frame_idx)) > self.elapsed_time:
                    self.frame_idx -= 1

            if not frame_data or frame_data.frame_idx != self.frame_idx:
                frame_data = self.get_frame_data(self.frame_idx)
                yield frame_data

    def generate_frames_non_real_time(self) -> Iterator[Optional[PlayerFrameData]]:
        # set frame_idx and elapsed_time to the start of the video
        self.go_to_start()

        min_frame = self.get_start_frame_idx()
        max_frame = self.get_end_frame_idx()
        self.frame_idx = min_frame

        while self.run:
            frame_data = self.get_frame_data(self.frame_idx)
            yield frame_data

            self.frame_idx += self.play_speed

            if self.frame_idx > max_frame:
                if self.loop:
                    self.frame_idx = min_frame
                else:
                    break
            elif self.frame_idx < min_frame:
                if self.loop:
                    self.frame_idx = max_frame
                else:
                    break

    def generate_frames(self) -> Iterator[Optional[PlayerFrameData]]:
        if self.real_time:
            yield from self.generate_frames_real_time()
        else:
            yield from self.generate_frames_non_real_time()
