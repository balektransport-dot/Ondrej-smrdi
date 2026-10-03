# novysurvival – stavebný systém

Stavanie v štýle Rust pre Unreal Engine 5 (C++), funguje aj v multiplayeri (všetko kontroluje server).

**Čo vie:**
- základ, podlaha, stena, zárubňa, dvere, strecha – všetko sa prichytáva na mriežku 3 × 3 m
- statika: keď zbúraš stenu, spadne aj to, čo na nej stálo
- materiály drevo → kameň → kov (vylepšenie pridá HP)
- búranie vráti časť materiálu (poškodený diel vráti menej)
- kladenie predmetov z inventára (pec, stôl…), pri zbúraní sa predmet vráti
- hologram: modrý = dá sa položiť, červený = nedá (a v rohu obrazovky je napísané prečo)

## Súbory

| Súbor | Čo robí |
|---|---|
| `BuildTypes.h` | typy dielov, materiály, mriežka a tvary dielov |
| `BuildPiece.h/.cpp` | jeden položený diel (actor) – HP, materiál, dvere |
| `BuildingSubsystem.h/.cpp` | ktoré miesta v mriežke sú obsadené + statika |
| `BuildInventory.h/.cpp` | napojenie na inventár |
| `BuildingComponent.h/.cpp` | stavanie z pohľadu hráča – toto pridáš na postavu |

## Ako to dostať do hry

1. Skopíruj priečinok `Source/novysurvival/Building` do svojho projektu do `Source/novysurvival/`.
2. Pravý klik na `.uproject` → **Generate Visual Studio project files** a projekt skompiluj.
   V `novysurvival.Build.cs` stačia bežné moduly `Core`, `CoreUObject`, `Engine`.
3. Otvor Blueprint postavy (napr. `BP_ThirdPersonCharacter`) → **Add** → **Building Component**.
4. Na skúšku zaškrtni v komponente **Free Build** – staviaš bez materiálu.
5. V Event Graphe postavy napoj klávesy na funkcie komponentu:

| Kláves (návrh) | Funkcia komponentu |
|---|---|
| B | `Toggle Build Mode` |
| ľavé tlačidlo myši | `Try Place` (ak `Is Build Mode`, inak útok/čokoľvek iné) |
| R | `Rotate Preview` (strecha, dvere, nový základ, predmet) |
| koliesko myši | `Select Next Piece` (hore = 1, dole = -1) |
| 1 – 6 | `Select Piece` (Foundation, Floor, Wall, Doorway, Door, Roof) |
| E | `Try Interact` – otvorí/zatvorí dvere |
| X | `Try Demolish` – zbúra diel, na ktorý mieriš (len v režime stavania) |
| U | `Try Upgrade` – drevo → kameň → kov (len v režime stavania) |

## Ako sa stavia

- Najprv **základ** na zem. Ďalšie základy sa prichytia k prvému – mier na jeho okraj.
- **Stena / zárubňa**: mier na základ blízko hrany, kam ju chceš.
- **Dvere**: mier na zárubňu.
- **Podlaha / strecha**: mier na vrch steny (dá sa aj 1 políčko do previsu vedľa podlahy).
- Základ musí byť na zemi, nič nesmie stáť v ceste (ani ty) a musíš byť dosť blízko.

## Inventár

Ceny sú v komponente v **Piece Defs** a používajú predmety `Wood`, `Stone`, `Metal`.
Ak sa tvoje predmety v inventári volajú inak (napr. `Drevo`), prepíš ich tam.

Inventár sa hľadá sám:
1. ak PlayerController, postava alebo PlayerState implementuje **BuildInventoryInterface**, použije sa ten,
2. inak sa nájde komponent, ktorý má v názve `SimpleInventorySystem`, a zavolajú sa jeho funkcie
   `Get Item Amount`, `Remove Item`, `Add Item`.

Keď to nefunguje, v **Output Log** si vyfiltruj `LogBuildInventory` – vypíše, čo našiel a aké má inventár funkcie.
Potom v Blueprinte postavy daj **Class Settings → Interfaces → Add → BuildInventoryInterface**
a v troch funkciách (`Build Get Item Amount`, `Build Remove Item`, `Build Add Item`) zavolaj svoj inventár.

## Predmety z inventára (pec, stôl…)

V komponente do **Prop Meshes** pridaj `ID predmetu → model`. Z inventára (napr. tlačidlo „Položiť“)
zavolaj `Select Prop` s ID predmetu – zapne sa hologram, ľavým tlačidlom ho položíš a predmet
sa z inventára odoberie. Zbúraním (X) sa vráti.

## Vzhľad

- **Ghost Material**: priehľadný materiál s vektorovým parametrom `Color` – krajší hologram (nepovinné).
- Farby materiálov: sprav Blueprint z `BuildPiece`, zmeň **Tier Colors** a daj ho do **Piece Class** v komponente.

---

# Ťažba zlata – bager, sklápač, triedička (low poly)

Bagrom naberáš hlinu z kopy, nasypeš ju do sklápača, odvezieš k triedičke a tá z nej vytriedi zlato.
Odpad vysype na kopu za sebou. Všetko je poskladané z jednoduchých tvarov (kocky, valce, kužele),
takže to vyzerá low poly a netreba žiadne modely. Kód je v `Source/novysurvival/Mining`.

| Súbor | Čo to je |
|---|---|
| `DigSite` | kopa hliny (ložisko so zlatom alebo vysypaná kopa) – zmenšuje sa, ako ju kopeš |
| `Excavator` | bager – pásy, otočná kabína, výložník, rameno, lopata |
| `DumpTruck` | sklápač – korba sa vyklápa |
| `WashPlant` | triedička – násypka, pás, točiaci sa bubon, stôl so zlatom |
| `MiningVehicle` | spoločný základ strojov (jazda, kamera, nastupovanie) |
| `DirtContainerComponent` | nádoba na hlinu (lopata, korba, násypka) |

## Ako to vyskúšať

1. Skopíruj priečinok `Source/novysurvival/Mining` do projektu a skompiluj.
   V `novysurvival.Build.cs` musia byť moduly `Core`, `CoreUObject`, `Engine`, `InputCore`.
2. Do levelu potiahni z **Place Actors** (alebo Content Browser → C++ Classes):
   - pár **DigSite** na zem (ložiská – v detailoch nastav **Initial Dirt** = koľko ton a **Gold Per Ton** = koľko gramov zlata na tonu),
   - **Excavator** vedľa nich,
   - **DumpTruck**,
   - **WashPlant** kúsok ďalej.
3. Spusť hru, dojdi k stroju a stlač **F** – nastúpiš. Znova **F** – vystúpiš.

Netreba nastavovať žiadne Input Actions, klávesy si stroje čítajú samy.

## Ovládanie

**Všetky stroje:** W/S jazda, A/D zatáčanie, myš kamera, F vystúpiť

**Bager:**

| Kláves | Čo robí |
|---|---|
| Q / E | otáčanie kabíny |
| šípka hore / dole | výložník hore / dole |
| šípka vľavo / vpravo | rameno k sebe / od seba |
| ľavé tlačidlo myši | zatvára lopatu – keď je špička lopaty v kope, naberá hlinu |
| pravé tlačidlo myši | otvára lopatu – úplne otvorená vysype hlinu (do korby, násypky alebo na zem) |

**Sklápač:** drž **medzerník** – korba sa vyklopí a hlina sa vysype vzadu.
Cúvni zadkom nad násypku triedičky a vyklop.

## Ako sa hrá

1. Bagrom otvor lopatu (pravé tlačidlo), spusti ju do kopy a zatváraj (ľavé tlačidlo) – naberie hlinu.
2. Otoč kabínu nad korbu sklápača a lopatu otvor – hlina sa nasype do korby.
3. Sklápačom zacúvaj k triedičke a vyklop korbu do násypky.
4. Triedička hlinu spracuje: zlato pribúda na stole (a na tabuli), odpad rastie na kope za bubnom.

Čo nie je v nádobe, padne na zem a vznikne z toho nová kopa – dá sa znova nabrať.

## Čo zatiaľ nie je

- stroje fungujú v singleplayeri (alebo pre hráča, ktorý hru hostí) – multiplayer pre ostatných hráčov je ďalší krok,
- predaj zlata za peniaze a vylepšovanie strojov,
- skutočné kopanie do terénu (teraz sa kope z kôp – ložísk, ktoré položíš do levelu),
- vlastné 3D modely – dajú sa neskôr vymeniť namiesto kociek.
