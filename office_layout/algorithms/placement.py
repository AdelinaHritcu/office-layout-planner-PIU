"""
Modul: placement.py

Responsabil tehnic: Codrin Fortoes (Backend Developer / Algoritmi)
Conform documentatiei proiectului (pag. 3) – implementarea logicii algoritmice
legate de plasarea obiectelor, analiza spatiala si integrarea cu GUI.

Scopul acestui fisier
---------------------
Acest modul contine toata logica *matematica* si *spatiala* legata de:
- plasarea obiectelor in planul biroului,
- detectarea coliziunilor,
- verificarea marginilor camerei,
- calculul distantelor dintre obiecte,
- repozitionarea corecta a obiectelor (drag & drop),
- functia de snap-to-grid.

Aici NU exista cod PyQt, NU exista QGraphicsItem — doar modele logice, coordonate,
latimi, inaltimi si algoritmi.

Ce trebuie implementat aici
---------------------------
1. Coliziunea intre doua obiecte
   - O functie de tipul:
       collides(obj_a, obj_b) -> bool
     care verifica suprapunerea a doua dreptunghiuri (AABB overlap).

2. Verificarea iesirii din camera
   - Functie:
       fits_in_room(obj, room_rect) -> bool

3. Verificarea daca un obiect poate fi plasat intr-o pozitie
   - Functie:
       can_place_object(layout_model, candidate_obj) -> (bool, message)
     care verifica:
       * coliziuni cu alte obiecte
       * iesirea din camera
       * distantele minime simple (nu regulile complexe din validation.py)

4. Mutarea unui obiect
   - Functie:
       move_object(layout_model, obj_id, new_x, new_y) -> (bool, message)
     care:
       * face check cu can_place_object inainte de a modifica modelul
       * daca pozitia este nevalida → NU modifica modelul

5. Snap to grid
   - Functie:
       snap_to_grid(x, y, grid_size) -> (int, int)
     folosita de interfata grafica inainte de repozitionare.

6. Calcul distanta intre doua obiecte
   - Functie de tipul:
       distance_between(obj_a, obj_b) -> float
     necesara ulterior pentru validari in `validation.py`.

Limite si principii
-------------------
Acest modul trebuie sa fie:
- pur algoritmic,
- testabil independent,
- fara efecte secundare grafice.

El este folosit direct de scene.py atunci cand user-ul:
- trage un obiect pe scena,
- incearca sa-l mute intr-o pozitie nevalida,
- interactioneaza cu layout-ul.

Modulul `validation.py` se bazeaza pe functiile de aici pentru verificari mai avansate
(reguli, distante sociale, acces coridoare etc.).
"""
