from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable, Iterator, List, Sequence, Tuple


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def normalized(self) -> "Rect":
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 0:
            x = x + w
            w = -w
        if h < 0:
            y = y + h
            h = -h
        return Rect(x, y, w, h)


def distance_points(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def point_in_rect(p: Tuple[float, float], r: Rect) -> bool:
    rr = r.normalized()
    x, y = p
    return (rr.left <= x <= rr.right) and (rr.top <= y <= rr.bottom)


def rects_intersect(a: Rect, b: Rect) -> bool:
    ra = a.normalized()
    rb = b.normalized()
    return not (ra.right <= rb.left or ra.left >= rb.right or ra.bottom <= rb.top or ra.top >= rb.bottom)


def rect_intersection_area(a: Rect, b: Rect) -> float:
    ra = a.normalized()
    rb = b.normalized()

    ix1 = max(ra.left, rb.left)
    iy1 = max(ra.top, rb.top)
    ix2 = min(ra.right, rb.right)
    iy2 = min(ra.bottom, rb.bottom)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def inflate_rect(r: Rect, margin: float) -> Rect:
    rr = r.normalized()
    return Rect(rr.x - margin, rr.y - margin, rr.width + 2 * margin, rr.height + 2 * margin)


def distance_point_to_rect(p: Tuple[float, float], r: Rect) -> float:
    rr = r.normalized()
    x, y = p
    cx = clamp(x, rr.left, rr.right)
    cy = clamp(y, rr.top, rr.bottom)
    return hypot(x - cx, y - cy)


def distance_rect_to_rect(a: Rect, b: Rect) -> float:
    ra = a.normalized()
    rb = b.normalized()

    if rects_intersect(ra, rb):
        return 0.0

    dx = 0.0
    if ra.right < rb.left:
        dx = rb.left - ra.right
    elif rb.right < ra.left:
        dx = ra.left - rb.right

    dy = 0.0
    if ra.bottom < rb.top:
        dy = rb.top - ra.bottom
    elif rb.bottom < ra.top:
        dy = ra.top - rb.bottom

    return hypot(dx, dy)


def snap_value_to_grid(v: float, grid: float) -> float:
    if grid <= 0:
        return v
    return round(v / grid) * grid


def snap_point_to_grid(x: float, y: float, grid: float) -> Tuple[float, float]:
    return snap_value_to_grid(x, grid), snap_value_to_grid(y, grid)


def world_to_cell(x: float, y: float, grid: float) -> Tuple[int, int]:
    if grid <= 0:
        raise ValueError("grid must be > 0")
    col = int(x // grid)
    row = int(y // grid)
    return row, col


def cell_to_world_center(row: int, col: int, grid: float) -> Tuple[float, float]:
    if grid <= 0:
        raise ValueError("grid must be > 0")
    x = (col + 0.5) * grid
    y = (row + 0.5) * grid
    return x, y


def rect_to_covered_cells(
    r: Rect,
    grid: float,
    max_rows: int,
    max_cols: int,
) -> List[Tuple[int, int]]:
    if grid <= 0:
        raise ValueError("grid must be > 0")
    rr = r.normalized()

    x1 = rr.left
    y1 = rr.top
    x2 = rr.right
    y2 = rr.bottom

    start_row = int(y1 // grid)
    end_row = int((y2 - 1e-9) // grid)
    start_col = int(x1 // grid)
    end_col = int((x2 - 1e-9) // grid)

    start_row = max(0, min(max_rows - 1, start_row))
    end_row = max(0, min(max_rows - 1, end_row))
    start_col = max(0, min(max_cols - 1, start_col))
    end_col = max(0, min(max_cols - 1, end_col))

    cells: List[Tuple[int, int]] = []
    for r_i in range(start_row, end_row + 1):
        for c_i in range(start_col, end_col + 1):
            cells.append((r_i, c_i))
    return cells


def neighbors_4(row: int, col: int) -> Tuple[Tuple[int, int], ...]:
    return ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
