from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import ceil, hypot
from typing import Any, Dict, List, Optional, Tuple

from office_layout.utils.geometry import (
    Rect,
    distance_rect_to_rect,
    rects_intersect,
    rect_to_covered_cells,
    world_to_cell,
)
from office_layout.models.object_types import ObjectType, get_type_info, is_walkable


@dataclass
class ValidationError:
    code: str
    message: str
    objects_involved: List[Any]


# ----------------------------
# Model adapters / helpers
# ----------------------------

def _iter_objects(layout_model: Any) -> List[Any]:
    if hasattr(layout_model, "all_objects") and callable(getattr(layout_model, "all_objects")):
        return list(layout_model.all_objects())
    objs = getattr(layout_model, "objects", None)
    if objs is not None:
        return list(objs)
    if hasattr(layout_model, "iter_objects") and callable(getattr(layout_model, "iter_objects")):
        return list(layout_model.iter_objects())
    raise AttributeError("LayoutModel must expose all_objects() (preferred) or objects/iter_objects().")


def _room_rect(layout_model: Any) -> Rect:
    if hasattr(layout_model, "get_room_rect") and callable(getattr(layout_model, "get_room_rect")):
        d = layout_model.get_room_rect()
        return Rect(float(d["x"]), float(d["y"]), float(d["width"]), float(d["height"])).normalized()

    rr = getattr(layout_model, "room_rect", None)
    if rr is not None:
        if isinstance(rr, dict):
            return Rect(float(rr["x"]), float(rr["y"]), float(rr["width"]), float(rr["height"])).normalized()
        if isinstance(rr, Rect):
            return rr.normalized()

    # fallback for your LayoutModel fields (room_width/room_height)
    if hasattr(layout_model, "room_width") and hasattr(layout_model, "room_height"):
        return Rect(0.0, 0.0, float(layout_model.room_width), float(layout_model.room_height)).normalized()

    raise AttributeError("LayoutModel must expose get_room_rect(), room_rect or room_width/room_height.")


def _get_grid_size(layout_model: Any) -> float:
    gs = getattr(layout_model, "grid_size", None)
    if gs is None:
        return 20.0
    try:
        v = float(gs)
    except Exception:
        return 20.0
    return v if v > 0 else 20.0


def _get_exit_points(layout_model: Any) -> List[Tuple[float, float]]:
    pts = getattr(layout_model, "exit_points", None)
    if not pts:
        return []

    out: List[Tuple[float, float]] = []
    for p in pts:
        if isinstance(p, dict):
            out.append((float(p["x"]), float(p["y"])))
        else:
            out.append((float(p[0]), float(p[1])))
    return out


def _ui_type(obj: Any) -> str:
    md = getattr(obj, "metadata", None)
    if isinstance(md, dict):
        v = md.get("ui_type")
        if isinstance(v, str) and v:
            return v

    t = getattr(obj, "type", None)
    if isinstance(t, ObjectType):
        return t.name.title()
    if isinstance(t, str):
        return t

    return "Unknown"


def _is_wall(obj: Any) -> bool:
    t = getattr(obj, "type", None)
    if t == ObjectType.WALL:
        return True
    return _ui_type(obj) == "Wall"


def _obj_rect(obj: Any) -> Rect:
    """
    Convention used in your project:
    - For most objects: obj.x/obj.y are top-left.
    - For walls saved by your scene sync:
        * horizontal: obj.x = left, obj.y = centerline_y, width >= height
        * vertical:   obj.x = centerline_x, obj.y = top, height > width
      width/height store wall bounding box sizes.
    """
    x = float(getattr(obj, "x"))
    y = float(getattr(obj, "y"))
    w = float(getattr(obj, "width"))
    h = float(getattr(obj, "height"))

    if _is_wall(obj):
        thickness = min(w, h)
        if w >= h:
            # horizontal: x is left, y is centerline
            return Rect(x, y - thickness / 2.0, w, thickness).normalized()
        # vertical: x is centerline, y is top
        return Rect(x - thickness / 2.0, y, thickness, h).normalized()

    return Rect(x, y, w, h).normalized()


def _rect_inside_room(r: Rect, room: Rect) -> bool:
    rr = r.normalized()
    rm = room.normalized()
    return rr.left >= rm.left and rr.top >= rm.top and rr.right <= rm.right and rr.bottom <= rm.bottom


def _rect_center(r: Rect) -> Tuple[float, float]:
    rr = r.normalized()
    return (rr.left + rr.right) / 2.0, (rr.top + rr.bottom) / 2.0


def _clamp_cell(cell: Tuple[int, int], w: int, h: int) -> Tuple[int, int]:
    r, c = cell
    r = 0 if r < 0 else (h - 1 if r >= h else r)
    c = 0 if c < 0 else (w - 1 if c >= w else c)
    return r, c


# ----------------------------
# Pathfinding (grid + A*)
# ----------------------------

def _neighbors_4(cell: Tuple[int, int], w: int, h: int):
    r, c = cell
    if r > 0:
        yield (r - 1, c)
    if r < h - 1:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c < w - 1:
        yield (r, c + 1)


def _astar_exists(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> bool:
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if w == 0:
        return False

    sr, sc = start
    gr, gc = goal
    if not (0 <= sr < h and 0 <= sc < w and 0 <= gr < h and 0 <= gc < w):
        return False
    if grid[sr][sc] == 1 or grid[gr][gc] == 1:
        return False

    open_heap: List[Tuple[int, Tuple[int, int]]] = []
    heappush(open_heap, (0, start))
    gscore: Dict[Tuple[int, int], int] = {start: 0}
    visited: set[Tuple[int, int]] = set()

    while open_heap:
        _, cur = heappop(open_heap)
        if cur in visited:
            continue
        visited.add(cur)

        if cur == goal:
            return True

        for nb in _neighbors_4(cur, w, h):
            r, c = nb
            if grid[r][c] == 1:
                continue

            tentative = gscore[cur] + 1
            if nb not in gscore or tentative < gscore[nb]:
                gscore[nb] = tentative
                f = tentative + abs(gr - r) + abs(gc - c)  # Manhattan
                heappush(open_heap, (f, nb))

    return False


def _build_occupancy_grid(layout_model: Any, cell_size: float) -> Tuple[List[List[int]], Rect, float]:
    room = _room_rect(layout_model)

    w = max(1, int(room.width // cell_size))
    h = max(1, int(room.height // cell_size))
    grid: List[List[int]] = [[0 for _ in range(w)] for _ in range(h)]

    def _mark_rect_as(value: int, r: Rect) -> None:
        rr = r.normalized()

        local = Rect(
            rr.left - room.left,
            rr.top - room.top,
            rr.width,
            rr.height,
        ).normalized()

        cells = rect_to_covered_cells(
            local,
            grid=cell_size,
            max_rows=h,
            max_cols=w,
        )

        for r0, c0 in cells:
            if 0 <= r0 < h and 0 <= c0 < w:
                grid[r0][c0] = value

    objects = _iter_objects(layout_model)

    # 1) Mark obstacles
    for obj in objects:
        ui = _ui_type(obj)

        # doors do not block; they will be "opened" later
        if ui == "Door":
            continue

        # Anything walkable should not block
        ot = getattr(obj, "type", None)
        if isinstance(ot, ObjectType) and is_walkable(ot):
            continue

        r = _obj_rect(obj)
        _mark_rect_as(1, r)

    # 2) Open doors (create walkable gaps), using padding so they reliably cut walls in the grid
    door_pad = max(cell_size * 0.6, 6.0)  # adjust if needed; 0.6 works well with 40px grid

    for obj in objects:
        if _ui_type(obj) != "Door":
            continue

        r = _obj_rect(obj).normalized()

        opened = Rect(
            r.left - door_pad,
            r.top - door_pad,
            r.width + 2.0 * door_pad,
            r.height + 2.0 * door_pad,
        ).normalized()

        _mark_rect_as(0, opened)

    # 3) Safety: ensure exits are not accidentally blocked by rounding
    exit_pts = _get_exit_points(layout_model)
    if exit_pts:
        for ex, ey in exit_pts:
            rr, cc = world_to_cell(ex - room.left, ey - room.top, cell_size)
            if 0 <= rr < h and 0 <= cc < w:
                grid[rr][cc] = 0

    return grid, room, cell_size


# ----------------------------
# Main validation
# ----------------------------

def validate_layout(layout_model: Any) -> List[ValidationError]:
    errors: List[ValidationError] = []

    objects = _iter_objects(layout_model)
    room = _room_rect(layout_model)

    # 1) Bounds check
    for obj in objects:
        r = _obj_rect(obj)
        if not _rect_inside_room(r, room):
            errors.append(
                ValidationError(
                    code="OUT_OF_BOUNDS",
                    message=f"{_ui_type(obj)} is outside room bounds.",
                    objects_involved=[obj],
                )
            )

    # 2) Collision check
    for i in range(len(objects)):
        a = objects[i]
        ra = _obj_rect(a)
        for j in range(i + 1, len(objects)):
            b = objects[j]
            rb = _obj_rect(b)
            if _is_wall(a) and _is_wall(b):
                continue
            if rects_intersect(ra, rb):
                errors.append(
                    ValidationError(
                        code="COLLISION",
                        message=f"{_ui_type(a)} overlaps {_ui_type(b)}.",
                        objects_involved=[a, b],
                    )
                )

    # 3) Minimum distance rules (per type)
    for i in range(len(objects)):
        a = objects[i]
        ta = getattr(a, "type", None)
        if not isinstance(ta, ObjectType):
            continue

        info_a = get_type_info(ta)
        ra = _obj_rect(a)

        for j in range(i + 1, len(objects)):
            b = objects[j]
            tb = getattr(b, "type", None)
            if not isinstance(tb, ObjectType):
                continue

            info_b = get_type_info(tb)
            rb = _obj_rect(b)

            d = distance_rect_to_rect(ra, rb)
            if ta == tb:
                required = max(float(info_a.min_distance_to_same_type), float(info_b.min_distance_to_same_type))
            else:
                required = max(float(info_a.min_distance_to_other), float(info_b.min_distance_to_other))

            if required > 0 and d < required:
                errors.append(
                    ValidationError(
                        code="DISTANCE_TOO_SMALL",
                        message=(
                            f"Distance between {_ui_type(a)} and {_ui_type(b)} is {d:.1f}, "
                            f"required ≥ {required:.1f}."
                        ),
                        objects_involved=[a, b],
                    )
                )

    # 4) Optional: clutter heuristic (soft warning)
    for i in range(len(objects)):
        a = objects[i]
        ca = _rect_center(_obj_rect(a))
        for j in range(i + 1, len(objects)):
            b = objects[j]
            cb = _rect_center(_obj_rect(b))
            if hypot(cb[0] - ca[0], cb[1] - ca[1]) < 25.0:
                errors.append(
                    ValidationError(
                        code="OVER_CROWDING",
                        message=f"Area looks cluttered near {_ui_type(a)} and {_ui_type(b)}.",
                        objects_involved=[a, b],
                    )
                )

    # 5) Optional: path existence to exit (grid-based)
    exit_pts = _get_exit_points(layout_model)
    if exit_pts:
        cell_size = _get_grid_size(layout_model)
        grid, room_r, cell = _build_occupancy_grid(layout_model, cell_size=cell_size)

        h = len(grid)
        w = len(grid[0]) if h > 0 else 0
        if w > 0:
            # Start point: center of the first non-wall object
            start_xy: Optional[Tuple[float, float]] = None
            for obj in objects:
                if _is_wall(obj):
                    continue
                start_xy = _rect_center(_obj_rect(obj))
                break

            if start_xy is not None:
                sx, sy = start_xy
                sr, sc = world_to_cell(sx - room_r.left, sy - room_r.top, cell)
                sr, sc = _clamp_cell((sr, sc), w, h)

                reachable = False
                for ex, ey in exit_pts:
                    gr, gc = world_to_cell(ex - room_r.left, ey - room_r.top, cell)
                    gr, gc = _clamp_cell((gr, gc), w, h)
                    if _astar_exists(grid, (sr, sc), (gr, gc)):
                        reachable = True
                        break

                if not reachable:
                    errors.append(
                        ValidationError(
                            code="NO_PATH_TO_EXIT",
                            message="No walkable path from layout to any exit point.",
                            objects_involved=[],
                        )
                    )

    return errors
