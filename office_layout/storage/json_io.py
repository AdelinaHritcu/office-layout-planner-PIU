"""
Modul: json_io.py

Rolul acestui fisier
--------------------
Acest modul se ocupa de salvarea si incarcarea layout-ului in/dintr-un fisier JSON.
Este singurul loc din aplicatie care interactioneaza cu fisierul pe disc pentru
persistenta datelor.

Aici NU exista logica grafica, NU se lucreaza cu PyQt si NU se modifica obiectele
din scena. Modulul lucreaza exclusiv cu LayoutModel si cu reprezentarea sa serializabila.

Ce trebuie implementat aici
---------------------------
1. Functia save_layout(path, layout_model)
   - Primeste un obiect LayoutModel si o cale de fisier.
   - Apeleaza layout_model.to_dict() pentru a obtine structura serializabila.
   - Salveaza acea structura ca JSON pe disc.
   - Creeaza fisierul daca nu exista, suprascrie daca exista.

2. Functia load_layout(path) -> LayoutModel
   - Deschide fisierul JSON si incarca dictionarul.
   - Apeleaza LayoutModel.from_dict(data) pentru a reconstrui modelul logic.
   - Intoarce un obiect LayoutModel complet populat.

Dependente
----------
- Are nevoie de layout_model.to_dict() pentru salvare.
- Are nevoie de LayoutModel.from_dict() pentru incarcare.
- Nu importa nimic din graphics/, placement.py sau validation.py.

Cine foloseste acest modul
--------------------------
- UI (main_window sau meniul File):
    * foloseste save_layout(...) cand utilizatorul alege "Save"
    * foloseste load_layout(...) cand utilizatorul deschide un fisier
- LayoutModel:
    * trebuie sa ofere metodele to_dict() si from_dict()
- Tester / Data Layout:
    * verifica daca salvarea si incarcarea produc acelasi rezultat (round-trip test)

Responsabilitati pe roluri
--------------------------
- Backend / Algoritmi (Codrin):
    * implementeaza functiile save/load si mecanismele de serializare/deserializare.
- PM / UI Design (Adelina):
    * defineste formatul JSON minim necesar pentru a reprezenta un layout complet.
- Frontend (Raluca):
    * integreaza butoanele si actiunile din GUI cu functiile save_layout() si load_layout().
- Tester (Gabriel):
    * testeaza consistenta datelor incarcate si integritatea fisierelor JSON.

Principiu important
-------------------
json_io.py nu trebuie sa modifice logica layout-ului.
El doar transforma LayoutModel in JSON si JSON inapoi in LayoutModel.
Daca structura layout-ului se schimba, doar to_dict() si from_dict() trebuie actualizate.

Acesta este modulul central pentru persistenta datelor aplicatiei.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from office_layout.models.layout_model import LayoutModel


def save_layout(path: str | os.PathLike, layout_model: Any) -> None:
    """
    Salveaza layout_model in fisier JSON la calea `path`.

    Cerinte:
    - apeleaza layout_model.to_dict() pentru structura serializabila
    - scrie JSON pe disc (creeaza fisierul daca nu exista, suprascrie daca exista)
    - fara logica grafica / PyQt / modificari ale obiectelor din scena
    """
    if layout_model is None:
        raise ValueError("layout_model must not be None.")

    if not hasattr(layout_model, "to_dict") or not callable(getattr(layout_model, "to_dict")):
        raise TypeError("layout_model must provide a callable to_dict() method.")

    target = Path(path)
    if target.suffix.lower() != ".json":
        # Nu e obligatoriu, dar ajuta consistenta.
        # Daca nu vrei restrictia, poti elimina acest if.
        raise ValueError(f"Invalid file extension for layout: '{target.suffix}'. Expected '.json'.")

    data = layout_model.to_dict()
    if not isinstance(data, Mapping):
        raise TypeError("layout_model.to_dict() must return a dict-like object (Mapping).")

    # Creeaza folderul parinte daca nu exista
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)

    # Scriere atomica: scriem intr-un fisier temporar apoi facem replace.
    tmp_path = target.with_suffix(target.suffix + ".tmp")

    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            f.write("\n")

        tmp_path.replace(target)
    finally:
        # Daca a aparut o exceptie inainte de replace, curatam tmp-ul daca exista.
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def load_layout(path: str | os.PathLike) -> LayoutModel:
    """
    Incarca layout-ul din fisier JSON si reconstruieste LayoutModel.

    Cerinte:
    - citeste JSON-ul in dict
    - apeleaza LayoutModel.from_dict(data)
    - intoarce LayoutModel complet populat
    """
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(f"Layout file not found: {source}")

    if source.suffix.lower() != ".json":
        raise ValueError(f"Invalid file extension for layout: '{source.suffix}'. Expected '.json'.")

    try:
        with source.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in layout file '{source}': {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Layout JSON root must be an object/dict.")

    if not hasattr(LayoutModel, "from_dict") or not callable(getattr(LayoutModel, "from_dict")):
        raise TypeError("LayoutModel must provide a callable from_dict(data) classmethod.")

    try:
        model = LayoutModel.from_dict(data)
    except Exception as e:
        raise ValueError(f"Failed to build LayoutModel from JSON in '{source}': {e}") from e

    return model


