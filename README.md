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

# Prístrojový panel kamióna (tachometer)

Panel sa kreslí sám kódom (žiadne textúry) vpravo dole na obrazovke:

- **otáčkomer** (0 – 3500 ot/min) so zeleným úsporným a červeným pásmom, v strede **zaradený stupeň** (N, R, 1, 2…)
- **kontrolky priamo v ciferníku**: smerovky (blikajú samy), stretávacie a diaľkové svetlá, parkovacia brzda,
  porucha motora, žhavenie, dobíjanie, tlak oleja, teplota chladiva, ABS
- dole v ciferníku **digitálna rýchlosť** v km/h, **počítadlo km** a **priemerná spotreba** (l/100 km)
- vedľa dva **ručičkové budíky**: **nafta** a **AdBlue** – pri nízkom stave sa v nich rozsvieti oranžová kontrolka
- po zapnutí zapaľovania sa na chvíľu rozsvietia všetky kontrolky (test), keď motor nebeží, svieti dobíjanie a olej

| Súbor | Čo robí |
|---|---|
| `Dashboard/TruckGaugeWidget.h/.cpp` | widget panelu – hodnoty, kontrolky a kreslenie |

## Ako to dostať do hry

1. Skopíruj priečinok `Source/novysurvival/Dashboard` do svojho projektu do `Source/novysurvival/`.
2. V `novysurvival.Build.cs` pridaj do `PublicDependencyModuleNames` moduly `"UMG", "Slate", "SlateCore"`:
   ```csharp
   PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "UMG", "Slate", "SlateCore" });
   ```
3. Pravý klik na `.uproject` → **Generate Visual Studio project files** a projekt skompiluj.
4. V Blueprinte vozidla (alebo PlayerControllera) v **Event BeginPlay**:
   **Create Widget** (Class: `Truck Gauge Widget`) → **Add to Viewport** → výstup si ulož do premennej, napr. `Panel`.
5. Na vyskúšanie bez vozidla zaškrtni na paneli **Demo Mode** (uzol `Set Demo Mode` hneď po Create Widget) –
   ručičky a kontrolky sa začnú hýbať samy.

## Napojenie na vozidlo (Event Tick)

| Čo | Uzol na `Panel` | Odkiaľ (Chaos Vehicle) |
|---|---|---|
| rýchlosť, otáčky, stupeň | `Set Vehicle State` | `Get Forward Speed` × 0.036 (= km/h), `Get Engine Rotation Speed`, `Get Current Gear` |
| nafta 0 – 1 | `Set Fuel Level` | tvoja nádrž: aktuálne litre / objem nádrže |
| AdBlue 0 – 1 | `Set Ad Blue Level` | tvoja nádrž AdBlue |
| spotreba a km | `Add Trip` | vzdialenosť za tick v km (rýchlosť km/h × Delta Seconds / 3600) a minuté litre za tick |
| kontrolky | `Set Warning` | napr. `Parkovacia brzda` = true, keď je zatiahnutá |
| zapaľovanie | `Set Ignition`, `Set Engine Running` | pri štarte / vypnutí motora |

- Priemerná spotreba sa z `Add Trip` počíta sama, `Reset Trip` ju vynuluje. Ak ju počítaš inak, nastav `Average Consumption`.
- Rezerva nafty a AdBlue sa rozsvieti sama pod `Low Fuel Threshold` / `Low Ad Blue Threshold` (12 % a 10 %).
- Smerovky stačí zapnúť (`Set Warning` → `Smerovka vlavo` = true), blikanie robí panel. Výstražné svetlá = obe smerovky.

## Nastavenie vzhľadu

- **Scale** – veľkosť panelu (1 = približne tretina výšky obrazovky).
- **Max Rpm**, **Green Rpm From/To**, **Red Rpm From** – rozsah otáčkomera a farebné pásma.
- **Needle Smoothing** – ako rýchlo ručičky dobiehajú hodnotu.
- Panel sa kreslí vždy do pravého dolného rohu plochy, ktorú dostane. Ak ho chceš inde, vlož ho do vlastného
  Widget Blueprintu do Canvas Panelu a nastav mu veľkosť a pozíciu.
