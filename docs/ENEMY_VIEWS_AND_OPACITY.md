# Gegner: Transparenzkorrektur, Richtungen und Kurvenansichten

Basis: Stage 5, `8e6b27aa0be29e82b27b615b76777791ee97fcab`.

## Ursache und Korrektur

Der Eindruck des durchscheinenden Hintergrunds lässt sich in den Quelldaten
bestätigen: Innerhalb der Flugzeugkörper stehen tatsächlich transparente
Index-0-Pixel. Der Importer verursacht diese Lücken nicht: Die aus den komprimierten
Runtime-Glyphen zurückgelesenen Alpha-Masken und RGB-Farben entsprechen exakt
den Quellen nach der Palettenumordnung. Es ist keine pauschale Alpha-/NCM-Verwechslung.

| Typ | Gefüllte Pixel je Phase | Davon zuvor ringsum eingeschlossene Lücken |
|---|---:|---:|
| Jäger | 1 | 0 |
| Bomber | 10 | 10 |
| Panzerflugzeug | 21 | 18 |
| Helikopter | 0 | 0 |

Die übrigen vier Stellen sind nach außen offene Risse innerhalb der gezeichneten
Rumpfkontur. `assets/art/spec-v2/source/enemy-opacity.json` dokumentiert alle
Koordinaten, Füllindizes und von Hand festgelegten Rumpf-/Tragflächen-Polygone.
Gefüllt wird ausschließlich vorheriger Index 0 mit einer vorhandenen dunklen
Körperfarbe. Keine bereits deckenden Pixel, Farben oder Flammenmasken werden
überschrieben. Die Reparatur wird vor dem Erzeugen aller drei Flammenphasen
angewandt und ist damit in jeder Phase identisch.

Beim Helikopter sind Rumpf und Cockpit deckend; Freiraum zwischen Rotorblättern
bleibt transparent. Auch bei allen 16 Panzer-Richtungs-/Kettenframes wurden keine
eingeschlossenen transparenten Löcher gefunden. Die Panzer bleiben unverändert.
Die Aussage bestätigt die geprüften Grafikdaten, nicht jede mögliche Ursache
von Anzeigeproblemen auf echter Hardware.

Vorher-Daten: `assets/art/enemy-views/source/before.json`. Der Export erzeugt
`generated/opacity-audit.png` auf Grün und Magenta mit gelb markierten Reparaturen
sowie einen maschinenlesbaren Bericht. Keine rechteckige Hintergrundfläche
wird in die eigentlichen RGBA-Assets eingebrannt.

## Neue Ansichten

Unter `assets/art/enemy-views/generated/`:

- Jäger und Helikopter: **16×16**, je N, NO, O, SO, S, SW, W, NW.
- Bomber und Panzerflugzeug: **32×32**, je geradeaus, linke und rechte Kurve.
- Jede Ansicht besitzt drei echte Flammen- bzw. Rotorphasen: insgesamt 66 Frames.
- Panzer bekommen auf Wunsch des Nutzers keine zusätzlichen Richtungen.

Die ursprünglichen Gegner schauen nach Süden. Die übrigen kleinen Ansichten
sind von der korrigierten kanonischen Grafik abgeleitet: exakte 90°-Drehungen
und Nearest-Neighbour-Abtastung für Diagonalen, ohne neue Farben. Einzelne Pixel
können bei der 45°-Rasterung entfallen/verdoppelt werden; es wird keine verlustlose
45°-Drehung behauptet. Die äußeren Pixelzentren passen in die jeweilige Zeichenfläche.

Die großen Kurvenposen sind eine neu konstruierte Perspektivverformung mit
asymmetrisch verkürzten Flügeln, Rollversatz und leichter Nase zur Kurvenseite,
keine bloße Drehung der Gesamtgrafik. Neu eingeschlossene einzelne Rasterlücken
außerhalb der Effektmaske werden in allen drei Phasen gleich deckend geschlossen;
die Koordinaten stehen als `derived_body_repairs` beim jeweiligen Pose-Datensatz.
Beim Helikopter werden solche Füllungen nicht auf die Rotorzwischenräume angewandt.
Die Körper bleiben pro Pose zwischen allen Phasen pixelgleich.

Paletten pro Typ bleiben **exakt RGB-identisch**, maximal 15 Farben plus Index 0.
Strips: `<typ>.png`, horizontal, **Pose zuerst, darin Phase 0/1/2**. Kleine Strips
sind 384×16, große 288×32. Die englischen Pose-IDs stehen im Manifest und in
`indexed-source.json`; WebP-Dateien zeigen jede Pose animiert, Vorschauen sind vergrößert.

Zusätzlich liegen indexierte Pixel, NCM, FCM und bewachte RRB-Spaltenstapel vor.
NCM: 16×8-Glyphen, zeilenweise Tile-Reihenfolge, linkes Pixel im LOW-Nibble.
FCM: 8×8-Tiles in zeilenweiser Reihenfolge. RRB: vertikale Spalte, Leer-Glyphe,
dann nächste Spalte; initiale Leer-Glyphe bei 0. `views.inc` enthält lokale
Basen mit LOW/HIGH-Anteil, Breiten/Höhen und vorgesehenen Palettenwerten.

**Dies sind Quellindizes.** Der Runtime-Importer `merge_bank()` sortiert Farben
nach Häufigkeit um. Beim Einbinden dessen Remap pro Typ anwenden und die lokalen
Glyphenbasen auf das Ziel versetzen. `$5f/$6f/$7f/$8f` allein stellt keine korrekte
Zuordnung der Quellindizes zur Runtime-Palette her.

## Was im Testbuild enthalten ist

Die **Transparenzreparaturen und die kleinere Münze sind im bestehenden Importweg
integriert**. Die bisherigen drei Süd-/Geradeaus-Phasen werden weiterhin verwendet.
Die neuen Richtungen/Kurven werden als vollständiger Asset-Satz geliefert;
eine automatische Auswahl entsprechend der Flugbahn ist noch nicht implementiert.

Der aktuelle Runtime-Satz benötigt 289 von 512 Glyphen, einschließlich acht
Raketenrichtungen. Ersetzt man die bisherigen zwölf Flugzeugframes (78 Glyphen)
durch alle 66 neuen Frames (324 Glyphen), wären es **535/512 Glyphen**. Der neue
Standalone-Satz hat einschließlich seiner eigenen Leer-Glyphe 325 Glyphen.
Vor einer vollständigen Runtime-Integration ist also Wiederverwendung/Deduplizierung
oder gezielte Pose-Auswahl nötig; kein bestehender Speicherbereich wird überlaufen.
Es wurden weder Laufzeitcode noch alte Releases oder Speicheradressen verändert.

## Kleinere große Bonusmünze

Die sichtbaren Münzdurchmesser sind jetzt **10 / 14 / 18 Pixel** statt 10 / 14 / 26.
Nur die große Münze wurde verkleinert; ihr Dollarzeichen hat wieder Glyphenskalierung 1.
ID `capsule_dollar_large`, 32×32-Zeichenfläche und bestehende Palette bleiben gleich.
Der normale Import übernimmt automatisch die kleineren sichtbaren Grenzen für
die abgeleitete Treffermaske. Schild, kleine und mittlere Münze bleiben pixelgleich.

## Reproduktion und Prüfung

```sh
python tools/export_spec_art.py
python tools/export_bonus_capsules.py
python tools/export_enemy_views.py
python tools/build.py --out build/enemy-game --kickass /path/to/KickAss65CE02-5.25.jar
python tools/check_spec_art.py
python tools/check_aircraft_animation.py
python tools/check_bonus_capsules.py
python tools/check_enemy_views.py
```

Normale Projektabhängigkeiten: Python, Pillow 12.3.0, NumPy 2.3.5. Der ursprüngliche
Referenzbogen im Repository wird für den allgemeinen Spec-Exporter weiterhin benötigt.
Reparaturkoordinaten, neue Perspektivtransformationen und Ableitungen sind offen
dokumentierte Pixelarbeit, keine als unverändert ausgegebenen Originalzeichnungen.

Geprüft: nur deklarierte Nullpixel geändert, andere Spec-Gruppen/Paletten
unverändert; 66 Frames, acht/drei eindeutige Ansichten, drei Phasen mit statischem
Körper, geschlossene Rumpfmasken, PNG/Alpha/Strips, NCM-/FCM-/RRB-Rücktest,
Dateihashes; tatsächliche komprimierte Runtime-Glyphen gegen die korrigierten
Quellfarben und Alpha zurückgeprüft. Münztest prüft die 10/14/18-Abstufung.
Alle drei Exporte werden auf Reproduzierbarkeit geprüft. Vollständiger Stage-5-
Build mit vorgeschriebenem, hashgeprüftem Assembler und D81-Rückleseprüfung erfolgreich.

**Kein neuer Emulator- oder Hardwaretest.** Bitte Transparenz auf wechselndem
Gelände, alle Flammen-/Rotorphasen, die verkleinerte Münze und deren Aufnahme testen.
