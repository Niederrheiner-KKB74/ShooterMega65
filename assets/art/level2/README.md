# Operation Canyon und Raffinerie

Die Karte scrollt von unten nach oben. 375 Zeilen bei 0,5 Pixeln pro Frame
ergeben bei 50 Hz vier Minuten vor Unterbrechungen durch Shops und Boss.

| Zeilen | Abschnitt |
|---|---|
| 0–95 | Sand, Dünen und Felsen vor dem Canyoneingang |
| 96–183 | Canyon mit gewundenem Fluss und Brücken bei 118 und 158 |
| 184–279 | Palmenoase und Außenposten, Shop bei 188 |
| 280–374 | Raffinerie mit Lagerhallen, Öltanks, Pumpen und Verladeplätzen. Boss bei 358, Shop bei 368 |

Gebäude und Zielklassen: Zelt (`checkpoint`), Funkmast (`radar`),
Kommandostand (`bunker`), Kisten (`crates`), Öltank, Pumpe und Kamin (`fuel`),
Werkstatt (`hangar`), Verladestation (`depot`), vier modulare Dachfelder (`hall`).
Der Zwei-Pixel-Rand bleibt bei jeder Gebäudegruppe und jedem Hallenfeld erhalten.
Brückendecks verwenden `structures`, Wasser und Ufer `water`.

Der 96×64-Kettenkreuzer liegt in `assets/art/boss-level2/generated/`. Die vier
Geschütze haben jeweils zwei aktive Ansichten und ein Wrack. Drei Phasen
animieren die Ketten. Der offene Motorraum ist ein eigenes Overlay.
`boss-animation.png` ist eine animierte PNG mit drei Frames.

Aus dem Repository-Stamm mit Python 3, Pillow und NumPy:

```sh
python assets/art/level2/source/generate.py
python tools/check_level2_art.py
```

Die Pixelquellen sind der Generator und die darin definierten indexierten Formen.
Er übernimmt die vollständige `fixed_targets`-Palette aus Level 1.
Die übrigen drei Landschaftspaletten und die Bosspalette sind für Level 2.
Grafik und Karte sind mit dem Level-Konverter geprüft. Wellen und Boss-Verhalten
folgen bei der Integration durch Claude. Hardwaretest steht aus.
