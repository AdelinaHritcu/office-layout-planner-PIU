"""
Modul: layout_model.py

Rolul acestui fisier
--------------------
Acest modul contine MODELUL LOGIC al layout-ului de birou.
Reprezinta "starea" aplicatiei: ce obiecte exista, unde sunt plasate, ce dimensiuni are
camera, unde sunt usile, zonele speciale etc.

Aici NU exista cod PyQt, NU existe item-uri grafice. Doar date pure si metode
de manipulare a datelor.

Ce trebuie definit aici
-----------------------
1. Clasa pentru un obiect plasat in layout
   - De exemplu:
       class LayoutObject:
           id: int
           type: ObjectType
           x: float
           y: float
           width: float
           height: float
           rotation: float
           metadata: dict (optional)
   - Obiectul trebuie sa poata fi serializat in/din JSON (vezi storage/json_io.py).

2. Clasa principala LayoutModel
   - Responsabilitati:
       * tine lista de LayoutObject
       * tine informatii despre camera (latime, inaltime, eventual grid_size)
       * stocheaza usi, zone de iesire, eventual marcaje pentru rute

   - Metode de baza:
       - add_object(obj: LayoutObject) -> None
       - remove_object(obj_id: int) -> None
       - get_object(obj_id: int) -> LayoutObject | None
       - all_objects() -> list[LayoutObject]
       - objects_by_type(object_type: ObjectType) -> list[LayoutObject]

   - Metode pentru integrare cu restul modulelor:
       - to_dict() -> dict  (pentru salvare JSON)
       - @classmethod from_dict(cls, data: dict) -> LayoutModel

3. Optional: helperi pentru scenarii frecvente
   - get_desks(), get_chairs(), get_walls() etc.
   - get_room_rect() -> (x, y, width, height)
   - get_doors() -> lista de obiecte de tip usa (daca sunt modelate ca obiecte)

Cine foloseste acest fisier
---------------------------
- storage/json_io.py:
    - salveaza si incarca LayoutModel in/din JSON.
- placement.py:
    - citeste si modifica LayoutModel cand se adauga sau se muta obiecte.
- validation.py:
    - parcurge LayoutModel pentru a verifica reguli, distante, rute.
- graphics/scene.py:
    - sincronizeaza elementele vizuale cu lista de LayoutObject din model.

Responsabilitati pe roluri
--------------------------
- Backend / Algoritmi (Codrin):
    - defineste structurile de date, metodele logice si contractul dintre model
      si modulele placement/validation/storage.
- UI Designer / PM (Adelina):
    - defineste ce informatii trebuie sa contina un layout din punct de vedere functional
      (ce obiecte minim trebuie sa putem reprezenta, ce se vede in UI).
- Frontend (Raluca):
    - foloseste LayoutModel ca sursa de adevar pentru ce trebuie desenat in scene.
- Tester / Data Layout (Gabriel):
    - testeaza consistenta modelului (adaugare, stergere, mutare, serializare/deserializare).

Ideea centrala
--------------
LayoutModel este "creierul de date" al aplicatiei: tot ce se vede in UI
si tot ce verifica algoritmii (placement, validation, rutare) se bazeaza pe el.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .object_types import ObjectType


# ---------------------------------------------------------------------------
# Representation of an object placed in the layout
# ---------------------------------------------------------------------------

@dataclass
class LayoutObject:
    """
    Represents a logical object placed in the layout (desk, chair, plant, wall, etc.).

    The coordinates (x, y), width, height, and rotation are expressed in the
    internal units of the application (typically the same coordinate system
    used by the graphics scene).

    This class does NOT care about how the object is drawn. It only stores:
    position, size, rotation, type, and optional metadata.
    """

    id: int
    type: ObjectType
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this object into a simple dictionary that can be serialized to JSON.
        """
        return {
            "id": self.id,
            "type": self.type.value,  # saved as string
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutObject":
        """
        Reconstruct a LayoutObject from a dictionary (e.g., loaded from JSON).
        """
        return cls(
            id=int(data["id"]),
            type=ObjectType(data["type"]),
            x=float(data["x"]),
            y=float(data["y"]),
            width=float(data["width"]),
            height=float(data["height"]),
            rotation=float(data.get("rotation", 0.0)),
            metadata=dict(data.get("metadata", {})),
        )


# ---------------------------------------------------------------------------
# Main layout model
# ---------------------------------------------------------------------------

class LayoutModel:
    """
    Logical model of the office layout.

    It stores:
    - room dimensions
    - the list of placed objects (LayoutObject)
    - optional information such as exits / doors

    This class has NO dependency on PyQt or any graphics code.
    """

    def __init__(
        self,
        room_width: float,
        room_height: float,
        grid_size: float = 50.0,
    ) -> None:
        self.room_width: float = room_width
        self.room_height: float = room_height
        self.grid_size: float = grid_size

        # dictionary id -> LayoutObject
        self._objects: Dict[int, LayoutObject] = {}

        # for generating new ids
        self._next_id: int = 1

        # optional: exit points (could also be modeled as LayoutObject)
        self.exit_points: List[Dict[str, float]] = []

    # ------------------------------------------------------------------
    # Basic object management
    # ------------------------------------------------------------------

    def _generate_id(self) -> int:
        new_id = self._next_id
        self._next_id += 1
        return new_id

    def add_object(
        self,
        object_type: ObjectType,
        x: float,
        y: float,
        width: float,
        height: float,
        rotation: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        forced_id: Optional[int] = None,
    ) -> LayoutObject:
        """
        Create and add a new LayoutObject to the model.

        If forced_id is provided (e.g. when loading from JSON), that id will be
        used and the internal _next_id will be adjusted accordingly. Otherwise,
        a new id is generated automatically.
        """
        if metadata is None:
            metadata = {}

        if forced_id is not None:
            obj_id = forced_id
            # keep _next_id consistent (next id must be larger than any existing one)
            self._next_id = max(self._next_id, obj_id + 1)
        else:
            obj_id = self._generate_id()

        obj = LayoutObject(
            id=obj_id,
            type=object_type,
            x=x,
            y=y,
            width=width,
            height=height,
            rotation=rotation,
            metadata=metadata,
        )
        self._objects[obj.id] = obj
        return obj

    def remove_object(self, obj_id: int) -> None:
        """
        Remove an object from the model, if it exists.
        """
        self._objects.pop(obj_id, None)

    def get_object(self, obj_id: int) -> Optional[LayoutObject]:
        """
        Return a LayoutObject by id, or None if it does not exist.
        """
        return self._objects.get(obj_id)

    def all_objects(self) -> List[LayoutObject]:
        """
        Return a list of all layout objects.
        """
        return list(self._objects.values())

    def objects_by_type(self, object_type: ObjectType) -> List[LayoutObject]:
        """
        Return all objects of a given logical type (e.g. all desks).
        """
        return [o for o in self._objects.values() if o.type == object_type]

    # ------------------------------------------------------------------
    # Room / area helpers
    # ------------------------------------------------------------------

    def get_room_rect(self) -> Dict[str, float]:
        """
        Return a simple dict describing the room rectangle.
        """
        return {
            "x": 0.0,
            "y": 0.0,
            "width": self.room_width,
            "height": self.room_height,
        }

    # ------------------------------------------------------------------
    # Serialization / deserialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the whole layout into a dictionary that can be serialized to JSON.
        Used by storage/json_io.py.
        """
        return {
            "room": {
                "width": self.room_width,
                "height": self.room_height,
                "grid_size": self.grid_size,
            },
            "objects": [obj.to_dict() for obj in self.all_objects()],
            "exit_points": list(self.exit_points),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutModel":
        """
        Rebuild a LayoutModel from a dictionary (typically loaded from JSON).
        """
        room = data.get("room", {})
        room_width = float(room.get("width", 800.0))
        room_height = float(room.get("height", 600.0))
        grid_size = float(room.get("grid_size", 50.0))

        model = cls(
            room_width=room_width,
            room_height=room_height,
            grid_size=grid_size,
        )

        for obj_data in data.get("objects", []):
            obj = LayoutObject.from_dict(obj_data)
            model.add_object(
                object_type=obj.type,
                x=obj.x,
                y=obj.y,
                width=obj.width,
                height=obj.height,
                rotation=obj.rotation,
                metadata=obj.metadata,
                forced_id=obj.id,
            )

        model.exit_points = list(data.get("exit_points", []))

        return model




