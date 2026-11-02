# Zerstörbare Bodenziele – Artwork für Stage 8

Grafiklieferung nach `docs/chatgpt_ground_targets.md` auf Branch `stage7`.
Quellenstand: `ebc6227f74e54a6cedb39d35f2f058304a2bb307`. Alle Dateien dieses
Pakets bleiben unter `assets/art/ground-targets/`; Programm, Level und bestehende
Assets werden nicht verändert. Den Einbau übernimmt Claude.

## Inhalt

| Teil | Lieferung |
|---|---|
| A | Alle sieben 32×32-Gruppen: Hangar, Depot, Checkpoint, Bunker, Radar, Treibstofftanks und Kisten; zusammen 28 zerstörte 16×16-Tiles |
| B | Leichte 16×16-Flak: acht Richtungen, zwei separate 16×16-Mündungsfeuerphasen, Wrack; echte Rohrspitzenkoordinaten |
| C | Optionale schwere 32×32-Doppel-Flak: gleiche Richtungen/Zustände, Mündungsfeuer weiterhin 16×16 |
| D | Alle 20 optionalen Stahl-/Ziegel-Hallenmodule, einschließlich `plain` |

**48 neue Tiles von höchstens 64.** Die verbindliche Datei ist
`generated/ground-targets.json`: ein Hex-Zeichen pro Pixel, von oben nach unten.
Keine neuen Tile-IDs werden bestehenden Levels zugeordnet.

## Gestaltung und Ränder

Die Ruinen behalten den Grundriss und erkennbare Reste ihres Gebäudetyps:
eingestürzte Hallendächer, umgestürzte Schranke, aufgebrochener Bunker, abgerissene
Radarschüssel, ausgebrannte Tanks und verstreute Kistenbretter. Keine Animation,
keine eingebrannten Rauchwolken oder Feueranimation. Das Spiel ergänzt Effekte.

Die äußeren **zwei Pixel jeder 32×32-Gruppe bleiben index- und RGB-identisch**
zum intakten Original. Im Inneren ändern sich je nach Gruppe 53–68 % der Pixel.
Alle Landschaftspixel verwenden Indizes 1–15: kein durchsichtiges oder schwarzes
Index-0-Loch. Die ursprüngliche Palette jedes Tiles bleibt erhalten; nur der
Bunker verwendet bereits die erweiterte `fixed_targets`-Palette.

Bei jedem einzelnen Hallenmodul bleiben sogar alle vier Zwei-Pixel-Ränder
identisch zum Original. Dadurch bleiben die vorhandenen Wand-/Dachanschlüsse
auch bei gemischten intakten und zerstörten Modulen erhalten. Das gilt für
gültige Anordnungen der bisherigen Eck-/Rand-/Mittelmodule; deren bauliche
Rollen ändern sich nicht. `hall-seams-preview.png` zeigt solche Mischungen.

## Geschütze und Palette

Detailüberarbeitung: schmale Stahlrohre mit dunklen Mündungen, getrennten
Rohrmanschetten und Rücklaufhülsen der Doppel-Flak. Wartungsluke, Nieten,
Panzerungsfugen und rote Kennzeichnung greifen die vorhandenen Panzer auf.
Größen, vollständige Palette, Sockel, Rohrspitzen, Feuerphasen und Wracks
bleiben gegenüber der ersten Lieferung unverändert.

Beide Geschütze verwenden `fixed_targets`. Der Sockel wird einmal gezeichnet
und unverändert unter jeden drehbaren Aufbau gelegt. Acht separat festgelegte
Geometrieprofile ergeben die Ansichten; kein Bild wird gedreht oder gespiegelt.
Kantenlicht und Laufreflexe bleiben im Weltkoordinatensystem oben links.
`construction.json` dokumentiert Sockel, Masken der beweglichen Oberteile und
alle Rohrspitzen. Beim schweren Geschütz nennt das verbindliche `muzzle` die
erste der beiden echten Rohrspitzen; beide stehen zusätzlich in `construction.json`.

Indizes 0–11 bleiben unverändert (insbesondere die von Panzern benutzten 1–11).
Nur die bisher freien Einträge werden belegt:

| Index | RGB | Verwendung |
|---|---|---|
| 12 | (16,18,22) | deckender Ruß und dunkle Wrackstellen |
| 13 | (72,58,47) | Asche und verbranntes Material |
| 14 | (225,65,24) | Warnoptik/Glut und Mündungsfeuer |
| 15 | (255,234,161) | helle Mündungsfeuerkerne |

Index 0 ist nur bei Geschütz-/Effektbildern transparent. Dunkle Laufmündungen
sind deckender Index 1, keine transparenten Bohrungen. Es wird keine zusätzliche
Palette benötigt. Die Ausgabe des offiziellen Prüfers enthält daher einen
erwarteten Informationshinweis zu den neuen Farben, keine verbleibende Sockelwarnung.

## Vorschauen und Reproduktion

- `destroyed-sheet.png`: Original links, zerstört rechts; alle Nutzbilder 1:1.
- `destroyed-sheet-4x.png`: exakt dieselbe Übersicht mit Nearest Neighbour 4×.
- `ruins-preview.png`: kompakte 3×-Ansicht der sieben Gebäudegruppen.
- `ground-gun.png`, `heavy-gun.png`: sämtliche Frames nebeneinander, 1× und 4×.
- `*-gun-1x.png` / `*-gun-4x.png`: reine horizontale Strips ohne Beschriftungen;
  beim schweren Geschütz bleiben die Flash-Frames 16×16 und sind im Strip vertikal zentriert.
- `*-gun-base.png`: die unveränderten Sockel separat zur Prüfung.
- `hall-seams-preview.png`: Beispielhallen intakt, gemischt und zerstört.

```sh
python -m pip install -r assets/art/ground-targets/source/requirements.txt
python assets/art/ground-targets/source/generate.py
python assets/art/ground-targets/source/verify.py
python tools/check_ground_targets.py
```

Python 3 und Pillow 12.3.0. Die Grafik ist neue native Pixelarbeit auf Basis der
ursprünglichen Paletten-/Tile-Indizes, keine verkleinerte KI-Illustration.
`source/intact-reference.json` archiviert die 48 intakten Referenztiles und
Paletten einschließlich ursprünglicher Tile-Namen/IDs, Commit und NCM-Prüfsumme.
Der Export verwendet diese geprüfte Momentaufnahme; bei späteren Tileset-
Änderungen müssen Referenz und Randprüfung bewusst aktualisiert werden.

## Prüfung und Status

Das **unveränderte** `tools/check_ground_targets.py` wurde vor dem PR als eigener
Prozess gegen die zugehörigen Stage-7-Originaldaten ausgeführt. Exit-Code 0,
`OK, no errors`. Vollständige Ausgabe: `validation/check_ground_targets.txt`.
Das Skript zählt acht Ansichten plus Wrack als „9 frames checked“; die zwei
zusätzlichen Flash-Frames prüft es separat. Pro Geschütz sind alle elf Frames vorhanden.

Zusatzprüfung: exakte Ränder aller 28 Gruppen-Tiles und aller 20 Hallenmodule,
keine Landschafts-Nullpixel, unveränderte geschützte Paletteneinträge, feste
Sockel an allen nicht vom Aufbau überdeckten Pixeln, sichtbare primäre/sekundäre
Rohrspitzen, Nutzbild-/Preview-Übereinstimmung, exakte 4×-Skalierung, Prüfsummen
und bytegleich reproduzierbarer Export.

**Nur Grafikdaten, noch nicht im Spiel integriert oder auf Hardware getestet.**
Kein Programm-/Level-/Release-Build wird als neue spielbare Funktion behauptet.
