# Auftrag an ChatGPT: Überarbeitung von PR #22 (Level 3 „Operation Offshore“)

Bitte **im selben Pull Request #22** (Branch `art/level3-offshore-carrier`, Basis `stage12`) nachbessern. Landschaft,
Animationen, Ruinen und Karte sind gut und bleiben unverändert. Formate und Grenzen wie in `docs/chatgpt_level3.md`;
`python3 tools/check_level3_art.py` muss danach weiter ohne Fehler laufen.

## 1. Wasserflugzeug und Marinehubschrauber neu zeichnen (wichtig)

Die Ansichten sind im Spiel nicht lesbar: Die geraden Richtungen wirken wie ein Stern oder Kreuz, die diagonalen
(`northeast`, `southeast`, `southwest`, `northwest`) wie Pixelrauschen, offenbar durch Drehen eines Bildes entstanden.

- **Alle 8 Richtungen von Hand zeichnen**, jede als klare Silhouette. Diagonalen nicht durch Drehen erzeugen.
- Vorbild für Lesbarkeit und Pixeldichte: der Jäger aus Level 1,
  `assets/art/enemy-views/generated/fighter-preview.png` und `helicopter-preview.png`.
- 1 Pixel dunkle Kontur, höchstens 5–6 Farben pro Bild, große ruhige Flächen, kein Dithering.
- **Wasserflugzeug**: gerade Tragflächen, schlanker Rumpf, **zwei Schwimmer** unter den Flügeln deutlich sichtbar,
  Propeller als heller Strich oder Scheibe vorn. Die Phasen 0–2 unterscheiden sich nur am Propeller (und evtl. an
  einer kleinen Auspuffflamme), Rumpf und Flügel bleiben pixelgleich.
- **Marinehubschrauber**: Rumpf mit Kabine und klar erkennbarem Heckausleger, Kufen oder Schwimmer, Rotor als
  dünne helle Linien. Die Phasen 0–2 unterscheiden sich nur am Rotor (verschiedene Winkel), der Körper bleibt
  pixelgleich.
- Die Front zeigt jeweils in die Richtung von `pose` (`south` = zum Spieler hin).

## 2. Flugzeugträger: mehr Schiff, weniger Schild

Der Rumpf wirkt mit 96×112 wie ein Wappenschild. Bitte als **langes Schiff** neu zeichnen:

- `body` **80×128** (höchstens 96×128): lange gerade Seiten, **spitzer Bug unten**, gerades Heck oben,
  **schräges Landedeck** mit Markierungen, **Inselaufbau an der rechten Seite** (Radar darauf), Katapultspur
  vorn zum Bug hin.
- Vier Geschütztürme an den Ecken bzw. Seiten des Decks, der Deckaufzug (`core`) in der Mitte des Decks.
- `placement.json` entsprechend anpassen: `body_size`, Türme, `core`, `rotors` (Radar), `spray` (Bugwelle am Bug,
  Kielwasser am Heck), `catapult`.
- Speicher: mit 80×128 etwa 256 von 324 Glyphen, das Prüfskript rechnet nach.

## 3. Klein: Patrouillenboot Ost/West

Die Gischtlinien um das Boot in den Ansichten `east` und `west` sind unruhig. Bitte wie bei `north`/`south` als
saubere Bugwelle und Kielwasser zeichnen.

## Checkliste

- [ ] Nur `assets/art/enemies-level3/` und `assets/art/boss-level3/` geändert
- [ ] `python3 tools/check_level3_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Neue Vorschauen: alle Richtungen beider Flugzeuge vergrößert (4×), Träger zusammengesetzt
