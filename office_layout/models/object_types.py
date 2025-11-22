"""
Modul: object_types.py

Rolul acestui fisier
--------------------
Acest modul defineste TIPURILE de obiecte care pot fi plasate in layout-ul de birou:
mese, scaune, plante, pereti, imprimante, sali de meeting etc.

Aici NU se lucreaza cu coordonate sau scene grafice. Aici definim:
- ce tipuri de obiecte exista,
- ce proprietati implicite au (dimensiuni, categorie),
- ce constrangeri sunt legate de tip (ex: distanta minima fata de alte obiecte).

Ce trebuie implementat aici
---------------------------
1. Enumerarea tipurilor de obiecte
   - O enumerare de tipul:
       class ObjectType(Enum):
           DESK = "desk"
           CHAIR = "chair"
           PLANT = "plant"
           WALL = "wall"
           PRINTER = "printer"
           MEETING_TABLE = "meeting_table"
     Valorile string trebuie sa fie stabile, pentru a fi folosite la salvare in JSON.

2. Descrierea metadata pentru fiecare tip
   - O structura (clasa sau dataclass) de forma:
       class ObjectTypeInfo:
           type: ObjectType
           default_width: float
           default_height: float
           min_distance_to_same_type: float
           min_distance_to_other: float
           category: str  # ex: "furniture", "decoration", "infrastructure"
   - Un dictionar global:
       OBJECT_TYPES: dict[ObjectType, ObjectTypeInfo]
     care descrie toate tipurile.

3. Functii helper
   - get_default_size(object_type) -> (width, height)
   - get_type_info(object_type) -> ObjectTypeInfo
   - is_walkable(object_type) -> bool
     (folosit de algoritmii de rutare pentru a decide daca se poate trece printr-o celula)

Cine foloseste acest fisier
---------------------------
- layout_model.py:
    - stocheaza pentru fiecare obiect tipul lui (ObjectType) si dimensiunile.
- placement.py:
    - are nevoie de dimensiunile implicite si eventual de categorii pentru plasare.
- validation.py:
    - foloseste regulile minime legate de tip (ex: anumite tipuri cer distante mai mari).
- graphics/:
    - mapeaza tipul de obiect la iconuri / culori / sprite-uri grafice.

Responsabilitati pe roluri
--------------------------
- Backend / Algoritmi (Codrin):
    - defineste structurile de tip, metadata si functiile helper necesare algoritmilor.
- Data Layout / Tester (Gabriel):
    - verifica faptul ca valorile (dimensiuni, distante) sunt realiste si coerente,
      testeaza ca noile tipuri nu sparg layout-ul.
- UI / Frontend (Raluca):
    - foloseste ObjectType pentru meniuri si pentru a afisa iconurile corespunzatoare.

Acest modul este "sursa de adevar" pentru ce obiecte exista si cum sunt ele definite.
Orice tip nou se adauga mai intai aici, apoi este folosit in restul aplicatiei.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple


# -----------------------------------------------------------
# Enumeration of object types
# -----------------------------------------------------------

class ObjectType(Enum):
    DESK = "desk"
    CHAIR = "chair"
    ARMCHAIR = "armchair"
    PLANT = "plant"
    WALL = "wall"
    PRINTER = "printer"
    MEETING_TABLE = "meeting_table"


# -----------------------------------------------------------
# Metadata for each object type
# -----------------------------------------------------------

@dataclass
class ObjectTypeInfo:
    type: ObjectType
    default_width: float
    default_height: float
    min_distance_to_same_type: float
    min_distance_to_other: float
    category: str      # "furniture", "decoration", "infrastructure"
    walkable: bool     # whether this object can be walked through (used for routing)


# -----------------------------------------------------------
# Definition of all object types
# -----------------------------------------------------------

OBJECT_TYPES: Dict[ObjectType, ObjectTypeInfo] = {
    ObjectType.DESK: ObjectTypeInfo(
        type=ObjectType.DESK,
        default_width=120,
        default_height=60,
        min_distance_to_same_type=50,
        min_distance_to_other=30,
        category="furniture",
        walkable=False,
    ),

    ObjectType.CHAIR: ObjectTypeInfo(
        type=ObjectType.CHAIR,
        default_width=40,
        default_height=40,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="furniture",
        walkable=False,
    ),

    ObjectType.ARMCHAIR: ObjectTypeInfo(
        type=ObjectType.ARMCHAIR,
        default_width=60,
        default_height=60,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="furniture",
        walkable=False,
    ),

    ObjectType.PLANT: ObjectTypeInfo(
        type=ObjectType.PLANT,
        default_width=40,
        default_height=40,
        min_distance_to_same_type=10,
        min_distance_to_other=10,
        category="decoration",
        walkable=False,
    ),

    ObjectType.WALL: ObjectTypeInfo(
        type=ObjectType.WALL,
        default_width=100,
        default_height=10,
        min_distance_to_same_type=0,
        min_distance_to_other=0,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.PRINTER: ObjectTypeInfo(
        type=ObjectType.PRINTER,
        default_width=50,
        default_height=50,
        min_distance_to_same_type=20,
        min_distance_to_other=20,
        category="infrastructure",
        walkable=False,
    ),

    ObjectType.MEETING_TABLE: ObjectTypeInfo(
        type=ObjectType.MEETING_TABLE,
        default_width=200,
        default_height=100,
        min_distance_to_same_type=50,
        min_distance_to_other=40,
        category="furniture",
        walkable=False,
    ),
}


# -----------------------------------------------------------
# Helper functions
# -----------------------------------------------------------

def get_type_info(object_type: ObjectType) -> ObjectTypeInfo:
    """
    Return the metadata (ObjectTypeInfo) for a specific object type.
    """
    return OBJECT_TYPES[object_type]


def get_default_size(object_type: ObjectType) -> Tuple[float, float]:
    """
    Return the default size (width, height) for the given object type.
    """
    info = OBJECT_TYPES[object_type]
    return info.default_width, info.default_height


def is_walkable(object_type: ObjectType) -> bool:
    """
    Return True if this object type is walkable (i.e., routing can pass through it).
    """
    return OBJECT_TYPES[object_type].walkable
