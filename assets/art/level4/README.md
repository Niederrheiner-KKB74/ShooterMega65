# Operation Iron City

Das Finale scrollt bei 50 Hz in rund vier Minuten durch vier Abschnitte.
Die durchgehende Hauptstraße ist fünf Tiles breit, die Seitenstraßen zwei.
Querstraßen verbinden sie. Der 15 Tiles breite Vorplatz bietet Raum für
den Kampf-Mech.

Dachaufbauten, Südfassaden und Schatten machen die Gebäude aus der
Draufsicht erkennbar. Ruhige Höfe trennen Backstein, Glas und Fabrikdächer.
Größere Ruinen zeigen eingestürzte Dachflächen und gebrochene Träger.
Schutt ragt stellenweise über die Bordsteine. Die Ausschnitte
`*-320x200.png` zeigen jeden Abschnitt in Spielauflösung.

| Zeilen | Abschnitt |
|---|---|
| 0–95 | Vorstadt mit Backsteinhäusern, Parks, Kratern und Autowracks |
| 96–183 | Fabriken, Schornsteine, Lagerhallen und Tanklager |
| 184–279 | Innenstadt mit Glasfassaden, Leuchtreklamen und Shop bei 188 |
| 280–374 | Festung und Vorplatz, Boss bei 352, Shop bei 368 |

Levelende bei 375. Gegnerwellen und Laufwege kommen aus der Spielintegration.

| Ziel | Typ |
|---|---|
| Lagerhaus und Hangar | `hangar` |
| Fabrik mit Schornsteinen | `bunker` |
| Tanklager | `fuel` |
| Container und Paletten | `depot`, `crates` |
| Radar und Kontrollposten | `radar`, `checkpoint` |
| Modulare Lager- und Fabrikdächer | `hall` |

Die äußeren zwei Pixel bleiben beim Wechsel zur Ruine erhalten. Feuer,
Schornsteinrauch und Leuchtreklame haben jeweils drei Phasen. Warnlichter
haben zwei Phasen. Die Karte verweist jeweils auf die Startphase.

Die 76 Gegnerframes decken Jet, Kampfhubschrauber, Quadrocopter,
zweibeinigen Mech und den Vierbeiner samt Wrack ab. Die 4×-Vorschauen
zeigen die Posen und Phasen auf hellem und dunklem Untergrund.
In den Vergleichsbögen `*-vergleich.png` stehen die Level-1-Referenzen
links und die überarbeiteten Gegner rechts, beide in 4×.

Der Endboss hat einen 112×64-Pixel-Rumpf, vier unabhängige Waffen und zwei
gegenläufig animierte Beine. Die Schulterwaffen sind Raketenwerfer, die
Armwaffen Kanonen. Die Brust öffnet sich über dem Reaktor. Flamme, Staub
und Drohnenstart haben je drei Phasen. `boss-animation.png` ist eine
animierte Vorschau des Laufzyklus.

## Reproduktion

Im Repository-Stamm mit Python 3, Pillow und NumPy:

```sh
python assets/art/level4/source/generate_city.py
python assets/art/enemies-level4/source/refine_enemies.py
python tools/check_level4_art.py
```

Die Grafik verwendet native Pixelgeometrie. `fixed_targets` übernimmt alle
16 Farben aus Level 1. Das Prüfprotokoll liegt in
`validation/check_level4_art.txt`. Spielintegration und Hardwaretest folgen.
