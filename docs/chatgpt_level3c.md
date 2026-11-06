# Auftrag an ChatGPT: Level 3 „Operation Offshore“ – zweite Überarbeitung

Level 3 läuft im Spiel und ist auf echter Hardware getestet. Landschaft, Inseln, Bohrinseln und Hafen sind sehr gelungen
und bleiben. Überarbeitet werden müssen die **Windräder**, **alle Gegner** und der **Flugzeugträger**.

**Basis-Branch ist `stage13b`.** Bitte einen neuen Pull Request gegen `stage13b` stellen und nur diese Ordner ändern:
`assets/art/level3/` (nur die Windrad-Tiles und ihre Vorschau), `assets/art/enemies-level3/`, `assets/art/boss-level3/`.
Die Karte `levels/level3.json` bitte **nicht** ändern (Wellen und Schiffe setzt Claude). Formate und Grenzen wie in
`docs/chatgpt_level3.md`; das Prüfskript wurde angepasst (vierte Palette, liegender Träger):

```sh
python3 tools/check_level3_art.py
```

## 1. Windräder: falsche Perspektive

Im Spiel sieht man auf die Windräder **von vorn**, als stünde man vor dem Rotor. Die Kamera schaut aber **von oben**
(leicht schräg von Süden, wie bei allen anderen Tiles). Von oben gesehen:

- Fundament als runde Plattform im Wasser, darauf der Turmfuß; der Turm selbst ist von oben kaum zu sehen (höchstens
  ein kurzer Schatten auf dem Wasser nach rechts unten).
- Oben die **Gondel** als kleines längliches Gehäuse, die Nabe vorn daran.
- Der **Rotor steht senkrecht** und ist daher von oben fast **von der Kante** zu sehen: die drei Blätter erscheinen als
  helle Striche in einer sehr flachen Ellipse quer zur Gondel (etwa 28–30 px breit, 6–8 px hoch). Beim Drehen ändern
  sich Länge und Lage der Striche in dieser flachen Ellipse.
- Weiter 32×32 (4 Tiles), **3 Phasen**, dieselben Tile-Namen und dieselbe Animation `turbine` in `animations.json`, damit
  die Karte unverändert bleibt. Dazu passende Vorschau in `animation-phases.png`.

## 2. Gegner: detaillierter, schlanker, farbiger

Die Gegner wirken plump und zu wenig detailliert, die Flugzeuge sind nur hellblau und grau. Bitte **alle Frames neu
zeichnen** (gleiche `group`, `pose`, `phase`, Größen und Anzahl wie bisher):

- **Schlanke Silhouetten**: Rumpf schmal, Flügel und Rotorblätter dünn; die Fläche des Bildes nicht ausfüllen. Ein
  16×16-Flugzeug ist etwa 13–14 px breit und hoch, Rumpf 3–4 px breit.
- **Mehr Details**: Cockpitglas (hell glänzend), Kennzeichen, Abgas/Propeller, Tragflächenränder heller, Schatten auf
  der rechten/unteren Seite, 1 px dunkle Kontur.
- **Farben** (je Palette 15 Farben plus Durchsichtig):
  - `air` (Wasserflugzeug): z. B. Marine-Dunkelblau mit **orange-gelben** Tragflächenspitzen und roten Kennzeichen,
    oder Seenot-Lackierung Orange/Weiß. Kräftig, damit es sich vom Wasser abhebt.
  - `heli` (Marinehubschrauber): z. B. **Olivgrün/Sand** mit schwarzen Streifen oder Dunkelgrau mit gelber
    Warnlackierung am Heck. Deutlich anders als das Wasserflugzeug.
  - Beide Flugzeuge müssen auf dunklem und hellem Wasser gut sichtbar sein.
- **Schiffe**: schlanke Rümpfe statt breiter Wannen, mit Deck-Details (Aufbauten, Masten, Rettungsboote, Poller,
  Wasserlinie rot), Bugwelle und Kielwasser an den Rändern durchsichtig.
  - `speedboat` 16×16: schmal, etwa 6–7 px breit (Nord/Süd) bzw. hoch (Ost/West), Kielwasser in 4 Phasen.
  - `patrol_boat` 32×32: Rumpf etwa 12 px breit bei Nord/Süd (bzw. 12 px hoch bei Ost/West), Brücke, Mast,
    Geschützsockel. Gischt nur an Bug und Heck.
  - `frigate` 32×64: Rumpf etwa 20 px breit, spitzer Bug unten, Aufbauten in der Mitte, Hubschrauberdeck am Heck,
    zwei Geschützsockel (Lage in `placement.json`, bisher `[8, 8]` und `[8, 36]`), Wrack brennend mit Schlagseite.
- **Neue vierte Palette `frigate`** in `palettes.json` (die Fregatte bekommt eigene Farben, z. B. Grau mit dunklem Deck
  und roter Wasserlinie; die Frames der Fregatte bekommen `"palette": "frigate"`). `ships` gilt weiter für Schnellboot
  und Patrouillenboot.
- Vorschauen bitte vergrößert (4×) auf dunklem **und** hellem Wasser.

## 3. Flugzeugträger: liegend und schmaler

Unter dem Träger bleibt zu wenig Platz für den Spieler. Bitte den Träger **um 90° gedreht** zeichnen: **liegend, Bug
nach links**, und etwas schmaler.

- `body` **höchstens 128×64**, empfohlen **128×56**: lange gerade Bordwände oben und unten, spitzer Bug links, gerades
  Heck rechts, schräges Landedeck, **Inselaufbau an der Oberseite** (Steuerbord), Katapultspur am Bug.
- Vier Geschütztürme an den Enden des Decks, der Deckaufzug (`core`, 32×32) in der Mitte.
- `rotor_0–2`: Radar auf der Insel (bis 32×32).
- `spray_0–2` (32×16): Bugwelle **links** am Bug und Kielwasser **rechts** am Heck, die Wellen laufen waagerecht.
- `deck_jet_0`, `deck_jet_1`: Jet auf dem Katapult am Bug, **Front nach links**, mit Dampf bzw. beim Abheben;
  `deck_jet_2`: im Flug, **Front nach unten** (zum Spieler).
- `placement.json` anpassen (`body_size`, Türme, `core`, `rotors`, `spray.offsets`, `catapult.offset`).
- Speicher: mit 128×56 etwa 230 von 324 Glyphen, das Prüfskript rechnet nach.

## Checkliste

- [ ] Basis-Branch `stage13b`; nur die genannten Ordner geändert, `levels/level3.json` unverändert
- [ ] `python3 tools/check_level3_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Windrad-Phasen, alle Gegner in allen Richtungen und Phasen (4×, dunkles und helles Wasser),
      Träger zusammengesetzt (Türme intakt/zerstört, Aufzug offen), Bugwelle, Jet-Start
