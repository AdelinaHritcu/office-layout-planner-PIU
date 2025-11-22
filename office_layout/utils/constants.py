"""
Modul: constants.py

Rolul modulului
---------------
Acest modul contine CONSTANTE globale folosite in intreaga aplicatie.
Valorile definite aici nu apartin unui subsistem anume (UI, grafica,
model logic, algoritmi), ci reprezinta configurari comune intregului proiect.

Ce ar trebui sa se afle aici
----------------------------
- dimensiuni implicite (ex: dimensiunea camerei, grid_size, item_size)
- grosimi standard (ex: grosimea peretilor)
- cai catre resurse (iconuri, layout-uri de exemplu)
- valori numerice folosite peste tot (pentru a evita "magic numbers")

Cine foloseste acest modul
--------------------------
- graphics/scene.py:
      pentru grid_size, wall_thickness, dimensiuni implicite.
- models/layout_model.py:
      poate folosi dimensiunile implicite ale camerei.
- algorithms/placement.py si validation.py:
      pentru valori globale folosite in calcule.

Responsabilitati pe roluri
--------------------------
- PM / UI (Adelina):
      stabileste dimensiunile implicite vizibile in UI.
- Frontend (Raluca):
      foloseste constante pentru a evita cifre hard-codate.
- Backend (Codrin):
      foloseste aceleasi constante in algoritmi.
- Tester (Gabriel):
      verifica faptul ca schimbarea unei valori afecteaza corect aplicatia.

Ideea centrala
--------------
constants.py este "sursa de adevar" pentru valori numerice folosite frecvent.
Daca un numar este reutilizat in mai multe module, trebuie definit aici.
"""

# Default room size (in grid units)
DEFAULT_ROOM_WIDTH = 10
DEFAULT_ROOM_HEIGHT = 8

# Size of a grid cell (in pixels)
GRID_SIZE = 40

# Default wall thickness (in pixels)
WALL_THICKNESS = 4

# Minimum margin between the room and the window (in pixels)
CANVAS_MARGIN = 20
