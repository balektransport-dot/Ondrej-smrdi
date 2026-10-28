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
| `naves_sklapaci_low_poly.py` | sklápacie návesy 8 / 9 / 10 / 11 m (2 až 3 nápravy, iba stredový rám, korba tvaru U, 6-stupňový teleskopický valec vpredu, zadné čelo na horných pántoch) |
| `naves_podval_low_poly.py` | podvalníky 12 / 14 / 16 m (2 až 4 nápravy, nízka plošina v jednej výške s krkom, malé dvojité kolesá, sklopné rampy, bez rezerv) |
| `naves_cisterna_low_poly.py` | cisterny 9,5 / 11,5 / 13,6 m (2 až 3 nápravy, iba stredový rám, oválna nádrž s 3 až 5 komorami, poklopy na pántoch, ochranné trubky, rebrík, ADR tabuľky, skrinka s ventilmi a dvierkami vzadu) |
| `domiesavac_low_poly.py` | domiešavače betónu 4x2 / 6x2 / 8x2 (bubon 4,4 / 5,4 / 6,4 m, asi 7 / 9 / 11 m³): šikmý rotujúci bubon s vonkajšími lopatkami, nasýpka, žľab s predĺžením (odložený pod bubnom alebo pracovná poloha), nádrž na vodu, rebrík |
| `odtahovky_low_poly.py` | odťahovky na pevnom podvozku, každá v európskom aj americkom štýle: plošinová 4x2 / 6x2 / 8x2 (sklopný podrám, plošina zjazdí šikmo na zem, navijak s hákom vytiahne auto) a ťažká 6x2 / 8x2 (otočný žeriav s hákom, podjazdové rameno, podpery, skrine s dvierkami) |
| `pickup_vozik_low_poly.py` | dva pickupy (dvojkabína 4 dvere a jednokabína 2 dvere; čierny pruh, ochranný rollbar, svetelná lišta, rúrová ochrana, veľké kolesá, ťažná guľa) a prívesy so spojkou: malý vozík 2,0 / 2,6 m, podval na auto 4,0 / 5,2 m (pevná mriežková paluba, dva výsuvné nájazdy, dvojmontáž kolies, navijak vytiahne auto), vozík na palety 3,0 / 4,2 m s EUR paletami, cisternový vozík 1,5 / 3 m³ (tvar cisterny s klenbami, poklopy a dvierka skrinky s ventilmi sa otvárajú, armatúra v rovnakom rozmere ako na cisternovom návese), vozík na drevo s kmeňmi (4,0 / 6,0 m), skriňový vozík 2,5 / 3,6 m (zadná rampa, bočné dvere); skontrolované rýchlou kontrolou (nič nelevituje, kolesá nepretŕčajú podlahou ani blatníkmi, náklad nepresahuje paletu); všetko demontovateľné po dieloch (uchyty) |
| `zeriav_low_poly.py` | autožeriav 40 t (3 nápravy, 4-dielne teleskopické rameno) a 80 t (4 nápravy, 5-dielne rameno), hladké zaoblené karosérie (kabína so šikmým čelným sklom, kryt motora, ramená), oceľové protizávažie so zdvíhacími okami, ryhovaná paluba nosiča pred a za vencom, červeno-biele výstražné pásy na podperách, protizávaží a zadnom nárazníku, hlava ramena s tromi kladkami a anemometrom, diely na seba presne dosadajú (spodok dielu, ktorý leží na inom, je rovný a nezaoblený), detaily (mriežky, stierače, zrkadlá, hadice, zvary), kontrolované rýchlou kontrolou (nič nelevituje, nič sa neprenika): riadené nápravy, 4 výsuvné podpery, otočná nadstavba s kabínou a protizávažím, rameno na teleskopickom valci zdvihu, kladka, lano a háčikový blok; všetko demontovateľné po dieloch (uchyty) |
| `drvic_low_poly.py` | pásový čeľusťový drvič kameňa na štrk: násypka s bočnými klapkami a roštom, vibračný podávač, čeľusťový drvič (pevná a kývajúca sa čeľusť, excentrický hriadeľ so zotrvačníkmi), motorový diel s dvierkami, výstupný pásový dopravník s kameňmi (7,6 m), vodný rozstrek, plošina s rebríkom, hromady (vstup, násypka, štrk); všetko demontovateľné po dieloch (uchyty) |
| `triedicka_low_poly.py` | pásová triediaca stanica materiálov: násypka s podávacím pásom, vibračné dvojsito, tri výstupné dopravníky (hrubé na osi, stredné vľavo, jemné vpravo) s kameňmi, motorový diel s dvierkami, rozstrek, hromady troch frakcií; všetko demontovateľné po dieloch (uchyty) |
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

## Rýchla kontrola modelov

`Nastroje/rychla_kontrola.py` (Blender + Cycles, asi 20 s): zo skriptu s modelom urobí jeden obrázok zo šiestich pohľadov (3/4 spredu a zozadu, bok, predok, zadok, zhora) pre ľubovoľnú snímku animácie a s `QV_CHECK=1` vypíše **levitujúce diely** (žiadny iný diel do 4 cm) a **prieniky dielov**; zámerné prieniky sa vyfiltrujú súborom výnimiek (príklad `Nastroje/rychla_kontrola_zeriav_vynimky.txt`). Popis premenných je na začiatku súboru. S `QV_CAMS` si zvolíš vlastné pohľady (detaily kolies, motora, kabíny; pri jednom pohľade sa uloží samostatný obrázok). Kde presne sa dva diely prenikajú vypíše `Nastroje/prieniky_kde.py` (zhluky trojuholníkov so svetovými súradnicami). Príklad: `SCRIPT=zeriav_low_poly.py QV_ROOT=Zeriav_40t QV_OUT=kontrola.png QV_FRAME=650 QV_CHECK=1 QV_IGN=Nastroje/rychla_kontrola_zeriav_vynimky.txt blender -b -P Nastroje/rychla_kontrola.py`.

## Autožeriav – ovládanie

Vlastnosti na koreňovom objekte `Zeriav_40t` / `Zeriav_80t` (panel N → Item): `Koleso_otocenie`, `Riadenie`, `Podpery_vysun`, `Podpery_spust` (0 až 0,7 podložky dosadnú, do 1 sa podvozok nadvihne), `Otocenie` (±360°), `Vyzdvih` (0 až 78°), `Vysun` (všetky stupne rámena), `Hak` (0 = pod hlavou, 1 = na zemi), `Dvere_nosica`, `Dvere_zerava`. Animácia 1 až 1000: jazda, podpery, rameno, otočenie, hák dole a hore, zloženie. Hák nemá rodiča (jeho poloha je driver zo svetovej polohy hlavy ramena), lano mieri z hlavy na hák. Diely sú na uchytoch `<Žeriav>_uchyt_<diel>`, zoznam v `Dokumentacia/Zeriav.txt`.

## Drvič a triedička – ovládanie

Vlastnosti na hlavnom objekte (panel N → Item): `Otacanie` (stupne zotrvačníkov, resp. fáza vibrácií sita), `Chod` (0 = stojí, 1 = beží: vibrácie podávača / sita a kývanie čeľuste), `Pas_pohyb` (metre pásu, listy a kamene bežia po slučke), `Nasypka_bocnice`, `Nasypka_naplnenie`, `Dvere_motora`; drvič má `Hromada_strk`, triedička `Hromada_hrube`, `Hromada_stredne`, `Hromada_jemne`. Animácia 1 až 1000 (rozbeh, plnenie násypky, rast hromád). Pásy sú zložené z uchytov `<Stroj>_uchyt_<id>` (rám, pás, kryt hlavy, dva bubny); listy pásu a kamene sú objekty s driverom z `Pas_pohyb`. Zoznamy dielov v `Dokumentacia/Drvic.txt` a `Dokumentacia/Triedicka.txt`.

## Návesy – ovládanie

- **Sklápací náves:** `Sklopenie` (0 až 1, korba sa zdvihne o 42 až 45°) a `Zadne_celo` (0 až 1, otvorí zadné čelo o 72°); ostatné vlastnosti ako pri plato návese (`Vyska_podvozku`, `Zdvih_napravy`, `Podpery`); náves má len stredový rám bez bočných líšt a bez rezerv.
- **Cisterna:** `Poklopy` (0 až 1, poklopy komôr sa otvárajú postupne od zadného) a `Dvere_skrinky` (0 až 1, dvere skrinky s ventilmi sa otvoria dozadu o 100°); ostatné ako vyššie.
- **Domiešavač:** `Boben_otacky` (kladné = miešanie, záporné = vyprázdňovanie, 1 = jedna otáčka), `Smyk_odlozeny` (1 = žľab leží dopredu pod bubnom, 0 = pracovná poloha), `Smyk_otocenie` (±100°), `Smyk_sklon` (5 až 25°), `Smyk_predlzenie` (0 = zložené, 1 = rozložené); podvozok ako pri nosičoch (`Vyska_podvozku`, `Zdvih_napravy`, `Vyklopenie_kabiny`, `Motor`).
- **Plošinová odťahovka:** `Plosina_sklon` (0 až 1), `Plosina_odsun` (0 až 1) a `Hak_k_autu` (0 až 1); odťahované auto je v scéne a jeho vytiahnutie nesú kľúče animácie (snímky 450 až 900).
- **Ťažká odťahovka:** `Podpery`, `Zeriav_otocenie` / `Strela_otocenie`, `Zeriav_zdvih`, `Zeriav_vysun`, `Hak_spustenie` (americká aj `Hak2_spustenie`), `Podjazd_zdvih`, `Podjazd_vysun` a `Skrine` (dvere skríň).
- **Podvalník:** `Rampa_L`, `Rampa_P` (0 = zložená na plošine, 1 = sklopená na zem), ostatné ako vyššie.
- **Pickup:** `Riadenie` (±35°), `Koleso_otocenie`, `Kapota`, `Zadne_celo`, `Dvere_pred_L/P`, `Dvere_zad_L/P` (0 až 1); gulu ťažného zariadenia riadi prázdny objekt `<Pickup>_gula`, podľa ktorého sa nakláňa zapriahnutý prívesok.
- **Prívesy:** spoločné `Koleso_otocenie`, `Opierne_koleso`, `Spojka`; podval na auto `Najazd_vysun`, `Najazd_sklon`, `Hak_k_autu`; malý vozík `Zadne_celo`; vozík na palety `Zadne_celo`, `Bocnice`, `Naklad` (počet paliet); cisterna `Poklopy`, `Dvere_skrinky`; vozík na drevo `Koliky`, `Naklad`; skriňa `Rampa`, `Dvere`.
- **Pneumatiky (pickup a prívesy):** telo pneumatiky je otočený prierez (zaoblené rameno, vypuklá bočnica s rebrami), pickup má hrubý terénny dezén s ramennými blokmi so zaoblenými hranami, prívesy dezén s pozdĺžnymi rebrami; matná čierna guma bez kovového lesku, disk má prírubu a gumový ventilok.
- **Prívesy – zadné svetlá a blatníky:** vodorovné zadné svetlá sú na zadnom nárazníku (väčší hlboký profil), blatníky kryjú kolesá len malým oblúkom nad osou; podval má na každej strane dve kolesá vedľa seba (`koleso_N_L_vnut` / `_von`).
- **Demontáž pickupu a prívesov:** každý diel je samostatný objekt `<Názov>_<diel>` na uchyte `<Názov>_uchyt_<diel>` (prázdny objekt v pivote dielu), animácia je na uchyte. Diel vymeníš tak, že zmažeš objekt dielu a nový diel s rovnakým pivotom dáš ako dieťa uchytu. Zoznam dielov je v `Dokumentacia/Pickup_vozik.txt`.
- Kráľovský čap je v počiatku návesu, spodok dosky je vo výške 1,31 m (vrch točne ťahača), takže hlavný objekt návesu stačí dať na miesto točne.
