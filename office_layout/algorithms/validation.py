"""
Modul: validation.py

Responsabil tehnic: Codrin Fortoes (Backend Developer / Algoritmi)
Conform documentatiei proiectului (pag. 3) – Codrin implementeaza algoritmii de
verificare a distantelor, rutare (Dijkstra / A*) si logica generala de validare.

Scopul acestui fisier
---------------------
Acest modul realizeaza *validarea complexa a intregului layout*: regulile din proiect,
distantele minime, detectarea zonelor supraaglomerate, pregatirea datelor pentru
rutare si verificarea accesibilitatii spatiilor.

Daca in `placement.py` verificam “poate sta obiectul A in acest loc?”, aici verificam:
“este intregul plan conform regulilor?”.

Ce trebuie implementat aici
---------------------------
1. Structura pentru erorile de validare
   - Clasa / dataclass:
       ValidationError(code, message, objects_involved)

2. Validarea distantelor minime
   - distante minime intre birouri
   - distante minime intre birou si perete
   - distante pentru trasee de evacuare (conform document pag. 1–2)

3. Validarea supraaglomerarii
   - identificarea zonelor unde prea multe obiecte sunt apropiate
   - marcarea lor ca “unsafe”, conform cerintei:
       “feedback vizual asupra spatiilor supraaglomerate sau sigure”
       (pag. 1)

4. Validarea accesului si coridoarelor
   - verificarea daca obiectele blocheaza rute importante
   - asigurarea unei latimi minime pentru coridoare (din rules.py)

5. Rutarea si accesibilitatea
   - implementarea sau apelarea algoritmilor A* / Dijkstra (pag. 2)
   - verificarea ca exista un traseu valid intre doua puncte:
       ex: birou → iesire / sala de meeting
   - detectarea obiectelor care blocheaza drumul

6. Functia principala:
       validate_layout(layout_model) -> list[ValidationError]
   Aceasta:
   - parcurge toate obiectele
   - aplica regulile de mai sus
   - returneaza lista erorilor (goala daca totul este ok)

Rolul acestui modul in proiect
------------------------------
- Ofera logica necesara pentru functiile de UX mentionate in document:
    • “verificarea automata a regulilor de distantare sociala” (pag. 1)
    • “afisarea distantelor dintre elemente”
    • “feedback vizual pentru zone sigure / nesigure”
    • “rutarea traseelor intre doua puncte”

- Scene-ul grafic (UI) doar afiseaza rezultatele.
- Validatorul decide daca layout-ul este corect din punct de vedere logic si algoritmic.

Principiu important
-------------------
Aici nu modificam layout-ul. Doar il evaluam si returnam erori.
GUI-ul decide cum sa le afiseze.

Codrin va folosi functiile din placement.py (coliziune, distante)
pentru a implementa regulile mai complexe descrise in document.
"""
