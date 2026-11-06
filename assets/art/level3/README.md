# Operation Offshore

Die Karte läuft bei 50 Hz rund vier Minuten. Zeile 0 liegt unten und Spalte 0
außerhalb des sichtbaren Spielfelds. In den Spalten 9–11 führt eine durchgehende
drei Tiles breite Fahrrinne durch alle Abschnitte.

| Zeilen | Abschnitt |
|---|---|
| 0–95 | Tiefe See, Palmeninseln mit Brandung, Riffe, Sandbänke und Leuchtfeuer |
| 96–183 | Ölfeld mit vier Bohrinseln, Tanks, Abfackel-Kaminen und Ölfilm |
| 184–279 | Shop auf offener See, Forschung, Solarfelder und Windpark |
| 280–374 | Marinehafen, Docks und Kielwasser. Freie Zufahrt in 336–351, Träger bei 352, Shop bei 368 |

Levelende bei 375. Formationen, Flugwege und Schiffsrouten kommen aus der
Spielintegration. Kielwasser im Tileset markiert die Anfahrt.

Zerstörbare Gruppen: Leuchtturm (`checkpoint`), Mast (`radar`), Bohrturm
und Tank (`fuel`), Kran (`depot`), Containerstapel (`crates`), Kommandomodul
(`bunker`) und Wohnmodul (`hangar`). Die modularen Deck- und Hallenfelder
verwenden `hall`. Alle 35 zerstörten Tiles halten die äußeren zwei Pixel
der zugehörigen Gebäudegruppe bzw. des Hallenfelds exakt ein.

Die Wasserpalette rotiert die Indizes 9–12 alle neun Frames (180 ms bei
50 Hz). Breite Flächen sind in festen, nahen Blautönen abgestuft.
Vereinzelte Lichtreflexe verwenden das Farbband. Die hellste Phase
wandert darin von oben nach unten. Riffe, Sandbänke, Bojen und
Ölfilme nutzen feste Farben. `water-cycle.gif` zeigt die vier Palettenphasen.

Die Windräder sind 32×64 Pixel groß und stehen auf Pylonen im Wasser. Die oberen
vier Tiles haben drei Rotorphasen, die unteren vier bilden Turm und Pylon.
`animation-phases.png` zeigt Rotoren, Kaminflammen und Antennenlichter.
`windpark-preview.png` zeigt die Platzierung im Level.

`assets/art/enemies-level3/generated/` enthält 75 Frames für Wasserflugzeug,
Marinehubschrauber, Schnellboot, Patrouillenboot und Fregatte samt Wrack.
Patrouillenboot und Fregatte tragen runde Sockel mit Koordinaten für die
drehbaren Geschütze. Die Einzelvorschauen zeigen alle Richtungen und Phasen.

Der Flugzeugträger in `assets/art/boss-level3/generated/` ist 128×56 Pixel
groß. Er hat vier getrennte Türme, einen Deckaufzug mit freiliegendem Reaktor,
ein drehendes Radar, Bugwellen und einen dreiphasigen Katapultstart.
`boss-preview.png` zeigt Gefecht und offenen Aufzug, `launch-phases.png`
den Start und `radar-wake-phases.png` die Effektphasen. `boss-animation.png`
ist eine animierte PNG.

## Reproduktion

Aus dem Repository-Stamm mit Python 3, Pillow und NumPy:

```sh
git worktree add --detach ../offshore-cycle-base 410124374a6873a7a827f45cf1763c49d149a353
python assets/art/level3/source/apply_water_cycle.py --base ../offshore-cycle-base
python tools/check_level3_art.py
```

Native indexierte Pixelgeometrie. `fixed_targets` übernimmt die vollständige
Level-1-Palette. `terrain.ncm.bin` speichert das linke Pixel im unteren Nibble.
Das Verzeichnis `generated/` enthält die verbindlichen Spieldaten und Vorschauen.
Das Prüfprotokoll einschließlich des Level-Konverters liegt in
`validation/check_level3_art.txt`. Die Vorschauen zeigen den Datenstand dieses Exports.
