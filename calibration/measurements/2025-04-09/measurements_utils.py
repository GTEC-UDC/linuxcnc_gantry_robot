from enum import StrEnum
from typing import Literal


class Direction(StrEnum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"


Coordinate = tuple[float, float]


def snake_move(
    start: Coordinate,
    end: Coordinate,
    turns: int = 0,
    direction: Literal["H", "V"] = "H",
) -> list[Coordinate]:
    if direction == "H":
        movements: list[Coordinate] = [(1, 0), (0, 1), (-1, 0), (0, 1)]
    elif direction == "V":
        movements: list[Coordinate] = [(0, 1), (1, 0), (0, -1), (1, 0)]
    else:
        raise ValueError(f"Invalid direction: {direction}")

    assert turns % 2 == 0, "turns must be even"

    num_mov = 2 if turns == 0 else 1 + 2 * turns
    coordinates: list[Coordinate] = [(0, 0)]

    for i in range(num_mov):
        mov_i = movements[i % 4]
        coord_i = coordinates[-1][0] + mov_i[0], coordinates[-1][1] + mov_i[1]
        coordinates.append(coord_i)

    x_factor = end[0] - start[0]
    y_factor = (end[1] - start[1])

    if direction == "V":
        x_factor /= (turns or 1)
    elif direction == "H":
        y_factor /= (turns or 1)

    return [
        (float(start[0] + x * x_factor), float(start[1] + y * y_factor))
        for x, y in coordinates
    ]
