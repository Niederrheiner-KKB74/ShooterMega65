# Auftrag an ChatGPT: Level 3 – bewegtes Meer (Color-Cycling) und hohe Windräder

Level 3 ist auf echter Hardware bestätigt. Zwei Wünsche des Besitzers: Das **Meer wirkt zu statisch**, und die
**Windräder** sollen **höher** wirken und **auf Pylonen im Wasser** stehen statt auf einer grauen Fläche.

**Basis-Branch ist `stage13b`.** Bitte einen neuen Pull Request gegen `stage13b` stellen und nur ändern:
`assets/art/level3/` und in `levels/level3.json` **nur die Karte** (`map`) im Bereich des Windparks.
`events`, `paths` und `formations` bitte nicht anfassen (Claude setzt Schiffe und Wellen danach neu).
Prüfen wie immer mit `python3 tools/check_level3_art.py` (Ausgabe in die PR-Beschreibung).

## 1. Color-Cycling für das Wasser (neu im Spiel)

Das Spiel kann jetzt einige Farben der Palette `water` im Kreis tauschen: Alle paar Frames rückt jede Farbe des
Bereichs eine Stelle weiter (die letzte wird zur ersten). Pixel mit diesen Indizes scheinen dann zu wandern. So
entstehen **laufende Wellen über das ganze Meer**, ohne zusätzliche Tiles.

Angabe in `animations.json` (neuer Schlüssel neben `animations`):

```json
"cycle": {"palette": "water", "first": 9, "count": 4, "period": 6}
```

- `first`/`count`: der Bereich der Palette `water`, der rotiert (3 bis 6 Farben, Indizes 1–15). `period`: Frames pro
  Schritt (2–32; 6 = gut 8 Schritte pro Sekunde).
- **Palette `water` neu ordnen**, Vorschlag:
  - 1–8: Wasser von tief nach flach, Sand unter Wasser (diese Farben bleiben ruhig)
  - **9–12: Wellenband** (z. B. Wasserton, etwas heller, Wellenkamm hell, wieder etwas heller), wird rotiert
  - 13–15: Grau, Hellgrau, Weiß (Masten, Bojen, Gischt, Ölfilm)
- **Wellenmuster zeichnen**: Auf den offenen Wasser-Tiles (tief, mittel, flach) **dünne Wellenlinien** mit den
  Indizes 9, 10, 11, 12 **in dieser Reihenfolge nebeneinander** (z. B. schräg oder waagerecht, 1 px pro Index),
  sparsam, damit es nicht flimmert: etwa 6–12 % der Pixel eines Tiles. Wenn die Farben rotieren, laufen die
  Wellenkämme dann sichtbar weiter. Muster über Tile-Grenzen hinweg nahtlos fortsetzen.
- Auch Brandung am Strand und Schaum um Riffe dürfen das Band nutzen (dann „atmet“ die Brandung).
- Alles, was **nicht** wandern soll (Riffe, Sandbänke, Ölfilme, Bojen, Masten), darf die Indizes 9–12 **nicht** verwenden.
- Die bisherige Animation **`glitter` entfällt** (das Cycling ersetzt sie): Tiles `glint_*` und den Eintrag in
  `animations` entfernen, in der Karte durch normale Wasser-Tiles ersetzen. Das macht 6 Tiles frei.
- Vorschau: `water-cycle.gif` (oder mehrere PNG-Phasen) mit einem Stück Meer, Brandung und Riff, damit man die
  Bewegung sieht.

## 2. Windräder: doppelt so hoch, auf Pylonen im Wasser

- Neues Windrad **32×64** (2 Tiles breit, 4 Tiles hoch). Blick weiter von oben, leicht schräg von Süden: Unten der
  **Pylon/Monopile im Wasser** (gelb-graues Übergangsstück mit kleiner Plattform und Leiter, Gischt am Fuß), darüber
  der **lange, schlanke Turm** nach oben (2–3 px breit, perspektivisch nach oben laufend), oben die **Gondel** und
  der **Rotor** (drei schlanke Blätter, wie in der jetzigen Draufsicht-Fassung).
- **Kein grauer Untergrund**: Der Hintergrund der Windrad-Tiles ist **Wasser** und muss nahtlos ins umgebende Meer
  übergehen. Deshalb die Windrad-Tiles in der Palette **`water`** anlegen (Turm und Gondel mit den Grautönen 13–15),
  mit demselben Wassermuster wie die Nachbar-Tiles.
- Animation `turbine`: nur die **oberen 2×2 Tiles** (Rotor und Gondel) haben **3 Phasen**; die unteren 2×2 Tiles
  (Turm und Pylon) sind fest. Das sind 4 + 4 × 3 = 16 Tiles statt bisher 12.
- Kurzer Schatten des Turms auf dem Wasser nach rechts unten ist willkommen.

## 3. Karte und Grenzen

- Im Windpark (etwa Zeilen 184–279) die Windräder auf das neue Format 2×4 umstellen. Zwischen den Windrädern
  weiter genug offenes Wasser lassen (Fahrrinnen mindestens 3 Tiles breit), damit Schiffe fahren können.
- Höchstens **126 Tiles** einschließlich aller Animationsphasen (die Grafikdatei des Levels fasst 16 KB);
  höchstens 256 verschiedene Kartenzeilen; 375 Zeilen wie bisher. Das Prüfskript rechnet nach.
- `glint_*` raus (−6), Windrad +4: das passt.

## Checkliste

- [ ] Basis-Branch `stage13b`; nur `assets/art/level3/` und die `map` in `levels/level3.json` geändert
- [ ] `python3 tools/check_level3_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Wasser-Cycling (Phasen oder GIF), Windrad mit allen Rotorphasen, Windpark im Level-Ausschnitt
