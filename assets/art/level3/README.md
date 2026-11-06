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

Wasser glitzert in drei Phasen, Turbinen haben drei Rotorstellungen,
Kaminflammen drei Phasen und Antennenlichter zwei. Die Karte verwendet
jeweils nur die erste Phase. `animation-phases.png` zeigt sämtliche Phasen.

`assets/art/enemies-level3/generated/` enthält 75 Frames für Wasserflugzeug,
Marinehubschrauber, Schnellboot, Patrouillenboot und Fregatte samt Wrack.
Patrouillenboot und Fregatte tragen runde Sockel mit Koordinaten für die
drehbaren Geschütze. Die Einzelvorschauen zeigen alle Richtungen und Phasen.

Der Flugzeugträger in `assets/art/boss-level3/generated/` ist 96×112 Pixel
groß. Er hat vier getrennte Türme, einen Deckaufzug mit freiliegendem Reaktor,
ein drehendes Radar, Bugwellen und einen dreiphasigen Katapultstart.
`boss-preview.png` zeigt Gefecht und offenen Aufzug, `launch-phases.png`
den Start und `radar-wake-phases.png` die Effektphasen. `boss-animation.png`
ist eine animierte PNG.

## Reproduktion

Aus dem Repository-Stamm mit Python 3, Pillow und NumPy:

```sh
python assets/art/level3/source/generate_terrain.py
python assets/art/level3/source/generate_vehicles.py
python tools/check_level3_art.py
```

Native indexierte Pixelgeometrie. `fixed_targets` übernimmt die vollständige
Level-1-Palette. `terrain.ncm.bin` speichert das linke Pixel im unteren Nibble.
Das Verzeichnis `generated/` enthält die verbindlichen Spieldaten und Vorschauen.
Das Prüfprotokoll einschließlich des Level-Konverters liegt in
`validation/check_level3_art.txt`. Spielintegration und Hardwaretest folgen.
