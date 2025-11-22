"""
Modul: geometry.py

Rolul modulului
---------------
Acest modul contine functii matematice si geometrice generale folosite pentru
calcule legate de layout: distante, coliziuni, verificari de suprapuneri,
aliniere la grid etc.

Functiile de aici NU depind de PyQt sau elemente grafice.
Ele lucreaza doar cu valori numerice si structuri de date simple.

Ce functii pot exista aici
---------------------------
- calculul distantei dintre doua puncte
- verificarea intersectiei intre doua dreptunghiuri
- functii de snap-to-grid
- functii optionale pentru rotatii / unghiuri

Cine foloseste acest modul
--------------------------
- algorithms/placement.py:
      pentru detectarea suprapunerilor si plasare valida.
- algorithms/validation.py:
      pentru verificarea distantelor, coridoarelor etc.
- graphics/scene.py:
      eventual pentru aliniere la grid si calcule de pozitionare.
- models/layout_model.py:
      pentru calcule de arie sau rect-uri.

Responsabilitati pe roluri
--------------------------
- Backend / Algoritmi (Codrin):
      implementeaza formulele si se asigura ca sunt corecte si eficiente.
- Tester (Gabriel):
      creeaza teste unit pentru verificarea corectitudinii functiilor.
- UI (Adelina, Raluca):
      nu modifica fisierul, dar se bazeaza pe comportamentul corect
      pentru o interactiune fluida in UI.

Ideea centrala
--------------
geometry.py trebuie sa contina functii PURE, independente si reutilizabile.
Orice calcul geometric general apartine acestui modul.
"""
