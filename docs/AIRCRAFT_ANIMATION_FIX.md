# Echte Fluganimationen und Bonus-Kapseln

Stand 01.11.2026, Basis `stage2` bei
`be8cc2ab3aab5dabd0198e858455d9af08774ee4`.

## Korrektur der bisherigen Varianten

Die bisherigen drei Frames pro Flugzeug enthielten unterschiedliche Zeichnungen
und waren deshalb keine gültigen Flammen-/Rotoranimationen. Auch die als
`flame_1..3` beschrifteten Playerbilder hatten wechselnde Flugzeugkörper.
Diese Einordnung wird mit diesem PR korrigiert.

Pro Typ wird jetzt ein kanonisches Grundbild verwendet. Rumpf, Flügel,
Cockpit, Position und Größe bleiben während der Schleife unverändert:

- Player: Frames 0,1,2 bilden die Geradeaus-Schleife mit ausschließlich
  wechselnden Heckflammen. Frame 4 ist pixelgleich zu Frame 0. Frames 3 und 5
  bleiben eigene Links-/Rechts-Steuerposen, keine Animationsphasen.
- Jäger, Bomber und Panzerflugzeug: jeweils ein festes Flugzeug mit drei
  Flammenphasen. Bei nach unten gerichteten Gegnern liegen die Auspuffflammen
  oben im Bild. Flammen ändern Länge und helle Spitzen, nicht den Rumpf.
- Helikopter: sauber rekonstruierter fester Rumpf, darüber drei Stellungen
  eines Zweiblattrotors (0/60/120 Grad). Rotorblätter dürfen den Rumpf innerhalb
  der Rotormaske verdecken; außerhalb dieser Maske bleibt jedes Pixel gleich.

Die unveränderten Grundzeichnungen sind mit ursprünglichen Paletten in
`assets/art/spec-v2/source/aircraft-animation.json` festgehalten. Die neuen
Effekte sind native Pixelkonstruktionen aus `tools/aircraft_animation.py`.
Beim Helikopter wurde der Rumpf neu konstruiert, damit keine alten Rotorblätter
in die statische Zeichnung eingebrannt bleiben. Dies wird nicht als Extraktion
oder bildgetreue Wiedergewinnung eines Originalsprites behauptet.

Flugzeuge verwenden eine Palette pro Typ, 12 Rumpffarben plus drei warme
Flammenfarben; transparente Farbe bleibt Index 0. Die bestehenden Palettenbänke
werden nicht vermehrt. Die gemeinsame Palettenreduktion verändert einzelne
Rumpffarbtöne gegenüber v2, aber nicht zwischen Phasen derselben Animation.
Helikopter behält seine bestehende Palette. Frames bleiben 32×24 (Player),
16×16 (Jäger/Helikopter) bzw. 32×32 (große Gegner), ohne Antialiasing und mit
binärem Alpha. Die Schleifen sind für etwa 100ms je Frame vorgesehen.

`generated/animation-mask-*.png` definiert die erlaubten Änderungsbereiche.
`animated-*.webp` zeigt die echten Schleifen vergrößert ohne Interpolation.
Die bisherigen PNG-Streifen, Indexquellen, Paletten, FCM/NCM, RRB-Daten und
Player-Sprite-Paare werden vom Exporter konsistent neu erzeugt.

```sh
python tools/export_spec_art.py
python tools/check_spec_art.py
python tools/check_aircraft_animation.py
```

Der neue unabhängige Prüfer vergleicht tatsächliche PNG-Pixel: jede Schleife
hat drei unterschiedliche Phasen, alle Änderungen liegen innerhalb der
Effektmaske, und der normale Playerframe entspricht der kanonischen Phase.
Steuerposen werden ausdrücklich aus der Flammen-Schleife ausgeschlossen.

## Bonus-Kapseln

Neue Pixelentwürfe unter `assets/art/bonus-capsules/`:

| Motiv | Rahmen | Sichtbarer Kapselkörper |
|---|---|---|
| `capsule_S` | 16×16 | 12×14, grüne Kapsel mit S |
| `capsule_dollar_small` | 16×16 | 10×12, kleine Geldkapsel |
| `capsule_dollar_medium` | 16×24 | 14×20, mittlere Geldkapsel |
| `capsule_dollar_large` | 32×32 | 24×28, große Geldkapsel |

Alle sind von oben/links beleuchtet, haben echte Transparenz und klar
konstruierte Buchstaben/Glyphen. Es sind vier statische Entwürfe, keine
zusätzlichen Animationen. Die Geldwerte/Bonuswirkung werden hier nicht festgelegt.
Die Maße erfüllen Breite ×16 und Höhe ×8 für Pixies. Jede Dollar-Kapsel hat
einen größeren Rahmen und einen größeren sichtbaren Körper als die vorherige.

Alle vier teilen **exakt die vorhandene Stage-2-HUD-/Bonuspalette in Bank 12**
(Colour-RAM `$cf`). Keine neue Palette, keine Umfärbung bestehender HUD-Farben.
Die Palette enthält höchstens 15 deckende Farben plus Transparenz; der Satz
benutzt nur eine Teilmenge. `source/capsules.json` hält Beschriftungen, Glyphen,
Körpergrößen und Palette fest. Geometrie und Export: `tools/export_bonus_capsules.py`.

Geliefert werden PNGs, Pixelquellen und rohe FCM/NCM/RRB-Daten mit Manifest.
Alle Binärdateien haben lokale Offsets/Indizes, keinen PRG-Ladeheader. NCM hat
linken Pixel im unteren Nibble, FCM 8×8-Tiles zeilenweise, RRB Spaltenstapel mit
Leer-Guards. Palettenregisterdaten sind planar und nibble-vertauscht.

```sh
python tools/export_bonus_capsules.py
python tools/check_bonus_capsules.py
```

Prüfungen umfassen exakte S-/Dollar-Glyphen, drei unterschiedliche Dollargrößen,
gemeinsame Palette/Alpha, FCM/NCM/RRB-Rückdekodierung und Leer-Guards.

## Laufzeitstatus

**Grafikdaten korrigiert/ergänzt und datengetestet; nicht neu in die Engine
integriert, nicht assembliert und nicht emulator-/hardwarebestätigt.** Die
vorhandenen Stage-2-Releases bleiben unverändert.

Claude hat wegen der falschen alten Animationen im aktuellen Importer
`AIR_FRAMES=1` und `PLAYER_STRAIGHT=4` gesetzt. Der neue Datensatz ist wieder
für drei Phasen geeignet. Zum Aktivieren müssen diese Auswahl und die
Player-Ruheanimation im Integrationsschritt ausdrücklich angepasst werden.
Das ist kein Grund, jetzt sämtliche Grafikphasen unbesehen zusätzlich in den
knappen Glyph-/PRG-Speicher zu laden: RRB-Basen, 256-Glyphen-Grenze und Staging
unter `$C000` nach dem tatsächlichen Import prüfen bzw. Frames streamen.
Kapseln ersetzen/erweitern den bisherigen Bonusplatzhalter erst nach explizitem
Import und Zuordnung der gewünschten Spielwirkungen.

Vorherige Dokumentation bleibt als historische Beschreibung des Entwurfs
erhalten; für Fluganimationen gilt nun diese Korrektur samt Manifest-Metadaten.
