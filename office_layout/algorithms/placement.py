from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Any, Iterable, Optional, Tuple


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


def _to_rect(obj: Any) -> Rect:
    if isinstance(obj, Rect):
        return obj

    if isinstance(obj, dict):
        x = obj["x"]
        y = obj["y"]
        w = obj["width"]
        h = obj["height"]
        return Rect(float(x), float(y), float(w), float(h))

    x = getattr(obj, "x")
    y = getattr(obj, "y")
    w = getattr(obj, "width")
    h = getattr(obj, "height")
    return Rect(float(x), float(y), float(w), float(h))


def collides(obj_a: Any, obj_b: Any) -> bool:
    a = _to_rect(obj_a)
    b = _to_rect(obj_b)

    if a.right <= b.left or b.right <= a.left:
        return False
    if a.bottom <= b.top or b.bottom <= a.top:
        return False
    return True


def fits_in_room(obj: Any, room_rect: Any) -> bool:
    o = _to_rect(obj)
    r = _to_rect(room_rect)

    return (
        o.left >= r.left
        and o.top >= r.top
        and o.right <= r.right
        and o.bottom <= r.bottom
    )


def distance_between(obj_a: Any, obj_b: Any) -> float:
    a = _to_rect(obj_a)
    b = _to_rect(obj_b)

    dx = 0.0
    if a.right < b.left:
        dx = b.left - a.right
    elif b.right < a.left:
        dx = a.left - b.right

    dy = 0.0
    if a.bottom < b.top:
        dy = b.top - a.bottom
    elif b.bottom < a.top:
        dy = a.top - b.bottom

    if dx == 0.0 and dy == 0.0:
        return 0.0

    return sqrt(dx * dx + dy * dy)


def snap_to_grid(x: float, y: float, grid_size: int) -> Tuple[int, int]:
    snapped_x = int(round(x / grid_size) * grid_size)
    snapped_y = int(round(y / grid_size) * grid_size)
    return snapped_x, snapped_y


def _iter_objects(layout_model: Any) -> Iterable[Any]:
    # cazul LayoutModel din layout_model.py
    if hasattr(layout_model, "_objects"):
        objs = getattr(layout_model, "_objects")
        if isinstance(objs, dict):
            return objs.values()
        return objs

    # fallback generic (daca alt model expune direct all_objects())
    if hasattr(layout_model, "all_objects"):
        return layout_model.all_objects()

    raise AttributeError("layout_model must expose _objects or all_objects()")



def _get_room_rect(layout_model: Any) -> Any:
    room = getattr(layout_model, "room_rect", None)
    if room is not None:
        return room

    if hasattr(layout_model, "get_room_rect"):
        return layout_model.get_room_rect()

    raise AttributeError


def _get_min_clearance(layout_model: Any) -> float:
    return float(getattr(layout_model, "min_clearance", 0.0))


def _get_obj_id(obj: Any) -> Optional[Any]:
    if isinstance(obj, dict) and "id" in obj:
        return obj["id"]
    return getattr(obj, "id", None)


def _can_place_internal(
    layout_model: Any,
    candidate_obj: Any,
    ignore_obj: Any | None = None,
    ignore_id: Any | None = None,
) -> Tuple[bool, str]:
    room_rect = _get_room_rect(layout_model)
    candidate_rect = _to_rect(candidate_obj)

    if not fits_in_room(candidate_rect, room_rect):
        return False, "Object is outside room bounds."

    min_clearance = _get_min_clearance(layout_model)

    for other in _iter_objects(layout_model):
        if other is None:
            continue

        if ignore_obj is not None and other is ignore_obj:
            continue
        if ignore_id is not None and _get_obj_id(other) == ignore_id:
            continue

        if collides(candidate_rect, other):
            return False, "Object collides with another object."

        if min_clearance > 0.0:
            dist = distance_between(candidate_rect, other)
            if dist < min_clearance:
                return False, "Object is too close to another object."

    return True, "Placement is valid."


def can_place_object(layout_model: Any, candidate_obj: Any) -> Tuple[bool, str]:
    return _can_place_internal(layout_model, candidate_obj)


def _find_object_by_id(layout_model: Any, obj_id: Any) -> Any:
    if hasattr(layout_model, "get_object"):
        return layout_model.get_object(obj_id)

    for obj in _iter_objects(layout_model):
        if obj is None:
            continue
        if _get_obj_id(obj) == obj_id:
            return obj

    raise KeyError(f"Object with id={obj_id!r} not found.")


def move_object(
    layout_model: Any, obj_id: Any, new_x: float, new_y: float
) -> Tuple[bool, str]:
    try:
        obj = _find_object_by_id(layout_model, obj_id)
    except KeyError as exc:
        return False, str(exc)

    current_rect = _to_rect(obj)
    candidate_rect = Rect(
        x=float(new_x),
        y=float(new_y),
        width=current_rect.width,
        height=current_rect.height,
    )

    ok, message = _can_place_internal(
        layout_model,
        candidate_rect,
        ignore_obj=obj,
        ignore_id=_get_obj_id(obj),
    )

    if not ok:
        return False, message

    if isinstance(obj, dict):
        obj["x"] = float(new_x)
        obj["y"] = float(new_y)
    else:
        setattr(obj, "x", float(new_x))
        setattr(obj, "y", float(new_y))

    return True, "Object moved successfully."
