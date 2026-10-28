# Blender – low poly modely pre Unreal Engine

Skripty pre Blender 3.0 a novší, ktoré vytvoria low poly (štýl Scrap Mechanic / Motor Town) modely vrátane pohyblivých dielov
a vyexportujú ich ako FBX do domovského priečinka (napr. `~/Nosice`). Každý skript je samostatný.

**Použitie:** Blender → záložka *Scripting* → pretiahni skript do textového editora → **Alt+P**.
Bez okna: `blender --background --python skript.py`. Do FBX sa exportuje každý diel zvlášť (pivot v kĺbe) a popis dielov a ovládačov je v `Dokumentacia/`.

## Skripty

| Skript | Čo vytvorí |
|---|---|
| `nosice_low_poly.py` | nosiče na pevnom podvozku 4x2 / 6x2 / 8x2: korba, sklápač, hákový nosič s kontajnermi, nosič dreva s hydraulickou rukou a valník s rukou |
| `tahace3_low_poly.py` | ťahače 4x2 / 6x2 / 8x2, kabína podľa modernej fotky (platí aj pre nosiče) |
| `tahace2_low_poly.py` | ťahače 4x2 / 6x2 / 8x2 s inou kabínou a nárazníkom |
| `tahace_low_poly.py`, `tahac_low_poly.py` | prvé verzie ťahačov |
| `naves_plachtovy_low_poly.py`, `naves_plato_low_poly.py` | plachtové a plato návesy (2 až 3 nápravy, vzduchové vankúše) |
| `podvozok_low_poly.py`, `nadrz_tocna_low_poly.py` | podvozok kamióna, nádrže a otočná |
| `motory_low_poly.py`, `prevodovky_low_poly.py` | motory R4 / R6 / V8 a prevodovky |
| `sklopka_low_poly.py`, `sklopka_v2_low_poly.py`, `vozik_low_poly.py` | sklopka (malý nákladiak) a vyklápací vozík |
| `minibager_low_poly.py`, `lopata_low_poly.py` | mini bager a lopata |
| `diely_low_poly.py`, `stavebnica_kamion_low_poly.py` | katalóg stavebných dielov a stavebnica kamióna |

## Nosiče – ovládanie

Každá nadstavba má vlastnosti na koreňovom objekte auta (panel N → Item) a animáciu, ktorú z nich riadi.

- **Hydraulická ruka (Drevo, Valník s rukou):** zložená ako zig-zag, 360° točňa, hlavné rameno, druhé rameno a dva teleskopické členy, každý s vlastným valcom.
  Drapák na drevo má dve čeľuste s valcami a pevný hák, rotátor sa točí bez obmedzenia. Podpery sa najprv vysunú do strany, noha sa otočí o 180° dolu, spustí sa na zem a nadvihne podvozok.
- **Hákový nosič:** teleskopické hákové rameno naberie kontajner zo zeme, vytiahne ho po sklopnom ráme a vyloží ho opačným postupom (snímky 460 až 900). Vlastnosti `Zdvih_ramu`, `Hak_uhol`, `Hak_vysun`.

Náhľady sú v `Nahlady/`, pomocný skript na render náhľadu v `Nastroje/render_preview.py`.
