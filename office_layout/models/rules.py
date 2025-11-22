"""
Modul: rules.py

Rolul acestui fisier
--------------------
Acest modul defineste REGULILE de business si parametrii configurabili
pentru validarea layout-ului de birou:
- distante minime intre obiecte,
- latime minima pentru coridoare,
- reguli de distantare sociala,
- capacitate maxima a incaperii etc.

Aici NU se fac calcule complicate. Aici doar definim valori, praguri si eventual
functii simple care expun aceste reguli.

Ce trebuie definit aici
-----------------------
1. Constante pentru distante minime
   - Exemplu:
       MIN_DESK_TO_DESK_DISTANCE = 1.5
       MIN_DESK_TO_WALL_DISTANCE = 0.5
       MIN_CORRIDOR_WIDTH = 0.8
   - Valorile pot fi in metri sau in unitati interne (grid), dar trebuie documentat clar.

2. Constante pentru limite de capacitate
   - Exemplu:
       MAX_PERSONS_PER_SQUARE_METER = 0.25
       MAX_ROOM_CAPACITY_DEFAULT = 20

3. Grupari de reguli pe categorii
   - De exemplu:
       SOCIAL_DISTANCE_RULES = {...}
       SAFETY_RULES = {...}
       COMFORT_RULES = {...}

4. Functii helper simple (optionale)
   - Exemplu:
       def get_min_distance_for_type(object_type: ObjectType) -> float:
           # intoarce distanta minima recomandata fata de alte obiecte
       def get_max_capacity_for_area(area: float) -> int:
           # calculeaza capacitatea maxima recomandata

Cine foloseste acest fisier
---------------------------
- validation.py:
    - aplica aceste reguli pentru a decide daca un layout este valid sau nu.
- placement.py:
    - poate folosi reguli de baza (ex: distante minime simple) pentru a bloca
      plasari evident invalide inca din faza de drag & drop.
- UI (optional):
    - poate afisa valorile regulilor in ecrane de "Settings" sau "Help".

Responsabilitati pe roluri
--------------------------
- Backend / Algoritmi (Codrin):
    - defineste interfata (numele constantelor si functiilor), astfel incat
      validation.py sa le poata folosi usor.
- Data Layout / Tester (Gabriel):
    - propune si ajusteaza valorile astfel incat sa fie realiste si sa respecte
      cerintele (distante, siguranta, confort).
- UI / PM (Adelina si Raluca):
    - decid ce reguli trebuie expuse spre utilizator (ex: slider pentru distanta minima,
      optiuni pentru nivel de supraaglomerare acceptat).

Ideea centrala
--------------
rules.py este locul central unde se definesc toate pragurile si regulile
care guverneaza layout-ul. Daca se schimba o regula de business, se modifica aici,
iar modulele placement.py si validation.py trebuie doar sa o foloseasca.
"""

from typing import Dict

from .object_types import ObjectType


# -----------------------------------------------------------
# 1. Minimum distance constants (in internal units)
#    (the same units as used in LayoutModel: pixels or cm)
# -----------------------------------------------------------

# distances between objects of the same type
MIN_DESK_TO_DESK_DISTANCE: float = 150.0
MIN_CHAIR_TO_CHAIR_DISTANCE: float = 80.0
MIN_ARMCHAIR_TO_ARMCHAIR_DISTANCE: float = 100.0

# distances between an object and a wall
MIN_DESK_TO_WALL_DISTANCE: float = 50.0
MIN_CHAIR_TO_WALL_DISTANCE: float = 40.0

# minimum corridor width (walkable path)
MIN_CORRIDOR_WIDTH: float = 90.0


# -----------------------------------------------------------
# 2. Capacity limits
# -----------------------------------------------------------

# maximum recommended number of people per unit of area
# (approximate value, can be adjusted by Gabriel)
MAX_PERSONS_PER_SQUARE_UNIT: float = 0.0025

# default recommended room capacity
MAX_ROOM_CAPACITY_DEFAULT: int = 20


# -----------------------------------------------------------
# 3. Rule groups (for reference or UI display)
# -----------------------------------------------------------

SOCIAL_DISTANCE_RULES: Dict[str, float] = {
    "desk_to_desk": MIN_DESK_TO_DESK_DISTANCE,
    "chair_to_chair": MIN_CHAIR_TO_CHAIR_DISTANCE,
    "armchair_to_armchair": MIN_ARMCHAIR_TO_ARMCHAIR_DISTANCE,
}

SAFETY_RULES: Dict[str, float] = {
    "desk_to_wall": MIN_DESK_TO_WALL_DISTANCE,
    "chair_to_wall": MIN_CHAIR_TO_WALL_DISTANCE,
    "min_corridor_width": MIN_CORRIDOR_WIDTH,
}

COMFORT_RULES: Dict[str, float] = {
    "max_persons_per_area": MAX_PERSONS_PER_SQUARE_UNIT,
}


# -----------------------------------------------------------
# 4. Simple helper functions
# -----------------------------------------------------------

def get_min_distance_for_type(object_type: ObjectType) -> float:
    """
    Returns the minimum recommended distance from other objects
    for the given object type (used for spacing and comfort rules).

    This is used mainly in validation.py, but can also be used in
    placement.py to prevent obviously invalid placements.
    """
    if object_type == ObjectType.DESK:
        return MIN_DESK_TO_DESK_DISTANCE
    if object_type == ObjectType.CHAIR:
        return MIN_CHAIR_TO_CHAIR_DISTANCE
    if object_type == ObjectType.ARMCHAIR:
        return MIN_ARMCHAIR_TO_ARMCHAIR_DISTANCE

    # no special rule for other object types
    return 0.0


def get_min_distance_to_wall(object_type: ObjectType) -> float:
    """
    Returns the minimum recommended distance from the wall
    for the given object type.
    """
    if object_type == ObjectType.DESK:
        return MIN_DESK_TO_WALL_DISTANCE
    if object_type == ObjectType.CHAIR:
        return MIN_CHAIR_TO_WALL_DISTANCE

    # no special rule for other object types
    return 0.0


def get_max_capacity_for_area(area: float) -> int:
    """
    Calculates the recommended maximum room capacity for a given area,
    using MAX_PERSONS_PER_SQUARE_UNIT.

    'area' must be in the same units as LayoutModel (width * height).
    """
    if area <= 0:
        return 0
    return int(area * MAX_PERSONS_PER_SQUARE_UNIT)


def get_min_corridor_width() -> float:
    """
    Returns the minimum recommended corridor width.
    """
    return MIN_CORRIDOR_WIDTH

