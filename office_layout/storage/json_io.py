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
