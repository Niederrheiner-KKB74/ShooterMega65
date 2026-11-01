# Shooter65 – Titel, Game Over und Level-1-Endgegner

Entwurf nach `docs/artwork_spec.md`, Abschnitte „Boss“ und „Title screen and
game-over screen“, Stage 6 bei `8716aaeb0c875d7c25f1f0626b7e0e8d77b0d128`.
Die ursprünglichen Motive bleiben erhalten. Das von Claude vorgegebene
Game-Over-Banner wird zusätzlich zum gewünschten 320×200-Vollbild geliefert.

## Titel und Game Over

Unter `assets/art/screens/generated/`:

| Asset | Größe | Palette | Einmalige 16×8-Tiles | Glyphenbytes |
|---|---|---|---:|---:|
| `title.png` | 320×200 | 16 Farben, eine Bank | 384 / 500 | 24576 |
| `game-over-banner.png` | 256×64 | 15 deckende Farben, eine Bank | 55 / 100 | 3520 |
| `game-over-full.png` | 320×200 | 16 Farben, eine Bank | 500 / 500 | 32000 |

Alle drei PNGs sind echte indexierte 4-Bit-PNGs mit 16 PLTE-Einträgen, ohne
Halbtransparenz oder zusätzliche Farben. Index 0 bedeutet bei statischen Screens
die Hintergrundfarbe, nicht PNG-Transparenz. Das Banner verwendet ausschließlich
Indizes 1–15, damit seine NCM-Fläche deckend bleibt.

**Titel:** Große Darstellung des blau-silbernen Players im Kampf gegen drei große
Bomber/Panzerflugzeuge über einer halb zerstörten Stadt. „Shooter65“ ist als
native Pixelschrift eingebrannt. Die Action liegt zwischen Logo und UI-Streifen.
Die untersten 320×24 Pixel (y=176..199) sind vollständig Hintergrundfarbe 0 für
„PRESS FIRE“ und Highscore. `title-preview.png` zeigt nur beispielhafte Spieltexte;
sie sind in `title.png` nicht enthalten.

**Game-Over-Banner:** Rahmen, zerstörter Player links und Stadtruinen rechts;
die zentrale Fläche x=64..191, y=6..57 bleibt für Engine-Texte frei. Keine
eingebrannten Wörter, Punktzahlen oder Eingabeaufforderungen in der Nutzgrafik.
`game-over-banner-preview.png` zeigt „GAME OVER“, Score und „PRESS FIRE“ exemplarisch.

**Vollbild-Alternative:** Das ursprünglich gewünschte 320×200-Bild mit großem
„GAME OVER“, abgestürztem zerstörtem Player und Ruinen liegt ebenfalls vor.
Es ist ausdrücklich eine Designalternative und ersetzt nicht unbemerkt das
spezifizierte 256×64-Runtime-Banner. Seine 500 Glyphen passen in das reine
32-KB-Glyphenbudget; Karte/Palette benötigen zusätzlichen Platz. Es ist nicht
für den kleineren Banner-Speicherbereich bestimmt.

### Bildschirmdaten

Zu jedem Motiv gehören `<name>.json`, `.ncm.bin`, `.map16.bin`, `.palette-map.bin`,
`.palette.rgb` und `.palette.palregs.bin`.

- JSON: alle Pixelzeilen, Palette, deduplizierte Tile-Karte und lokale Palettennummer
  jedes 16×8-Tiles; Hintergrund-/Textzonen und vorgesehene Rolle.
- NCM: 64 Byte pro 16×8-Glyphe, linkes Pixel im LOW-Nibble; erste Begegnung beim
  zeilenweisen Durchlauf bestimmt die lokale Glyphen-ID.
- Map: zeilenweise lokale 16-Bit-Glyphen-IDs, Little Endian; 20×25 Zellen bei
  Vollbildern, 16×8 beim Banner. Keine versteckte Landschaftsspalte.
- Palette-Map: ein Byte pro Zelle, hier überall 0 für die einzige **lokale** Bank.
- RGB: 16 RGB-Tripel, 48 Byte. Registerdaten: getrennte R/G/B-Ebenen mit
  getauschten Nibbles. Noch keine festen Hardware-Banknummern oder Ladeadressen.

Die Stadtszenen wurden mit der eingebauten `image_gen`-Funktion erzeugt, mit
den tatsächlich aktuellen Player-/Gegnergrafiken als Identitätsreferenz.
Die unveränderten KI-Szenen, das Referenzblatt und die vollständigen Prompts
liegen unter `source/`. Das sind **KI-generierte Szenen**, keine als handgemalt
ausgegebenen Pixeloriginale. Die reproduzierbare Konvertierung verwendet
Nearest Neighbour, eine explizite feste 16-Farben-Palette und native Pixelschrift.
Die Titel-Action wird zwischen den reservierten Bereichen eingepasst. Originale
bleiben erhalten; hochaufgelöste Quellen sind nicht die Ingame-Nutzgrafiken.

## Quadrocopter-Endgegner

Unter `assets/art/boss-level1/generated/` liegt ein vollständig neuer nativer
Pixelentwurf. Hauptkörper **96×64**, Blick von oben, Front nach unten.
Eine einzige gemeinsame Palette mit 15 deckenden Farben plus transparentem
Index 0 für Körper, Türme, Rotoren, Reaktorkern und Mündungsfeuer.

| Komponente | Grafikdaten | Instanzen |
|---|---|---|
| Hauptkörper | 96×64, ein statisches Bild | 1 |
| Geschütztürme | Je 16×16: Süden, Südosten, zerstört; vier individuelle Markierungen | 4 getrennte Schadensobjekte |
| Rotor | 32×32, drei echte Phasen als horizontaler Strip | 4 visuelle Instanzen mit Phasenversatz |
| Freigelegter Kern | 32×32-Overlay | Nach dem letzten zerstörten Turm |
| Mündungsfeuer | 16×16, zwei Phasen als horizontaler Strip | Optional am feuernden Turm |

Die Rotoren sind nur visuelle Animation, **keine zusätzlichen abschießbaren
Boss-Teile**. Es gibt genau vier erforderliche, separat abschießbare Geschütztürme.
Die Rotorbilder werden im Grafikpack nur einmal pro Phase gespeichert und für
alle vier Positionen wiederverwendet.

`placement.json` definiert alle Boss-lokalen Positionen, Turm-IDs und Rechtecke:

| Turm | Offset | Grafikgröße |
|---|---|---|
| `turret_nw` | (30, 8) | 16×16 |
| `turret_ne` | (50, 8) | 16×16 |
| `turret_sw` | (30, 40) | 16×16 |
| `turret_se` | (50, 40) | 16×16 |

Vorgesehene Zustandsfolge: `turrets_active` → nach Zerstörung **aller vier** IDs
`body_vulnerable` → Boss besiegt, wenn danach die Rumpf-HP auf null fallen.
Der Rumpf ist vorher unverwundbar. Kern-Overlay bei (32,16), vorgeschlagenes
Boss-lokales Kern-Trefferrechteck (40,24,16,16). HP und Angriffsmuster bleiben
Aufgabe des Spiels. Andere Geschützrichtungen können aus Süden/Südosten gedreht
werden. Mündungsfeuer darf über die 96×64-Körpergrenze hinausragen.

`assembled.png`, `all-turrets-destroyed.png` und `animated-boss.webp` sind
zusammengesetzte Vorschauen; die Türme sind nicht in die Rumpfgrafik eingebrannt.
Zeichenreihenfolge: Körper, Rotoren, freigelegter Kern, Türme, optionales Feuer.
Alle Rumpfschatten sind deckende Indizes; die Prüfung findet keine eingeschlossenen
transparenten Löcher. Transparenz an Bauteilrändern/Overlay-Flächen ist beabsichtigt.

### Boss-Budget und Import

19 Einzelgrafiken: 1 Körper, 1 Kern, 3 Rotorphasen, 12 Turmzustände/-richtungen,
2 Feuerphasen. Konservativ einschließlich Leer-/Wachglyphen:

| Anteil | 16×8-Glyphen |
|---|---:|
| Körper | 54 |
| Kern | 10 |
| Rotorphasen | 30 |
| Vier Türme, je drei Bilder | 36 |
| Mündungsfeuer | 6 |
| Initiale Leer-Glyphe | 1 |
| **Gesamt** | **137 = 8768 Byte** |

Mit einer 48-Byte-Palette sind es 8816 Byte Grafik/Palette, unter 9 KiB (9216).
Alle vier Rotor-Instanzen nutzen die gleichen drei Bilder. Kein zweiter großer
Körperframe wird benötigt; das kleine Kern-Overlay zeigt die zweite Schadensphase.

`indexed-source.json`, `palette.rgb`, `palette.palregs.bin` sowie `.indices.bin`,
`.ncm.bin`, `.fcm.bin`, `.rrb.bin` und `boss-frames.inc` liegen bei. FCM: 8×8-Tiles
zeilenweise; NCM: 16×8-Tiles zeilenweise, LOW-Nibble links. RRB: pro 16px-Spalte
alle vertikalen Glyphen, dann eine Leer-Glyphe; ganz vorne eine Leer-Glyphe bei 0.
Tabellen verwenden lokale Basen mit LOW/HIGH-Anteil. Beim Import auf Zieladresse
versetzen und eine Boss-Palettenbank auswählen oder per vorhandenem Importer
RGB-identisch remappen. Die Metadaten sind ein **Artwork-/Platzierungsvertrag**,
kein bereits existierendes Level-JSON- oder Engine-Bossformat.

## Reproduktion und Status

```sh
python -m pip install -r tools/screen-boss-requirements.txt
python tools/export_screen_art.py
python tools/export_boss_level1.py
python tools/check_screen_boss_art.py
```

Prüfung: native Dimensionen und echte 16-Einträge-PNG-Paletten, Tile-Budgets,
vollständige NCM-/Map-/Paletten-Rücktests, freie Textbereiche; 96×64 geschlossener
Bossrumpf, vier getrennte Turmpositionen und Abhängigkeiten, drei Rotorphasen,
Alpha/Strips, NCM-/FCM-/RRB-Rücktests, Komponentenkomposition, Dateihashes und
Grafikbudget. Export mit den archivierten Quellen ist bytegleich reproduzierbar;
ein erneuter KI-Aufruf muss nicht identische Szenen erzeugen.

**Noch nicht ins Spiel integriert, nicht im Emulator oder auf Hardware getestet.**
Keine Änderungen an Spielcode, Levelablauf oder alten Releases. Boss-Kollision,
HP-/Turmzustände, Schüsse, Loader, Screen-Umschaltung und Palettenrestaurierung
muss die kommende Engine-Stufe umsetzen. Deshalb wird kein neuer Spielbuild
oder ein spielbarer Boss behauptet.
