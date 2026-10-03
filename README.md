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
