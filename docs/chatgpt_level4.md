# Auftrag an ChatGPT: Level 4 „Operation Iron City“ (Finale: Stadt, Mechs, Mech-Boss)

Spiel: **Shooter65**, vertikaler Shooter für den MEGA65 (Repository `Niederrheiner-KKB74/ShooterMega65`).
**Basis-Branch ist `stage14`.** Bitte einen Pull Request gegen `stage14` stellen.

Level 1–3 sind fertig und auf Hardware bestätigt. Level 4 ist das **Finale**: eine **zerstörte Großstadt**. Gegner am
Boden sind **Mechs** (laufende Kampfroboter) statt Panzer, in der Luft **moderne Jets, Kampfhubschrauber und
Quadrocopter-Drohnen**. Der Endboss ist ein **großer, animierter Kampf-Mech**.

Gesucht sind **Grafik und Karte**. Bitte nichts an `src/`, `tools/` oder an Level 1–3 ändern. Wellen, Wege der Mechs
und das Verhalten setzt Claude. Formate wie in Level 3 (`docs/chatgpt_level3.md` bis `chatgpt_level3d.md`); Vorlage
für alle Dateien sind die Ordner von Level 3.

| Teil | Inhalt | Ordner / Datei |
|---|---|---|
| A | Stadt-Tileset 16×16 mit Animationen | `assets/art/level4/generated/` |
| B | Zerstörte Varianten der Gebäude | `assets/art/level4/generated/ground-targets.json` |
| C | Karte | `levels/level4.json` |
| D | Gegner von Level 4 | `assets/art/enemies-level4/generated/` |
| E | Endboss: Kampf-Mech | `assets/art/boss-level4/generated/` |

Vor dem Pull Request prüfen und die Ausgabe in die PR-Beschreibung kopieren:

```sh
python3 tools/check_level4_art.py
```

## Allgemein

- Pixelgenau, Draufsicht leicht schräg von Süden, Licht von oben links, wie bisher. Index 0 in Tiles verboten, in
  Objekten durchsichtig. Pro Tile/Objekt genau eine Palette mit 16 Einträgen.
- **Stil**: wie Level 1, aber **kantiger und moderner**: harte Kanten, abgeschrägte Panzerplatten, Leuchtakzente
  (Cyan, Orange, Rot), dunkle Grundtöne mit hellen Kanten. Abwechslung in den Farben (nicht nur Grau): Backstein,
  Beton, Asphalt, Rost, verbranntes Grün, Glas mit Spiegelungen, Feuerschein.

## Teil A: Tileset

Format wie Level 3 (`terrain.ncm.bin`, `level-example.json`, `manifest.json`, Vorschauen). Höchstens **126 Tiles**
einschließlich Animationsphasen. Vier Paletten mit **neuen Namen**:

| Palette | Inhalt | Regel |
|---|---|---|
| `streets` | Straßen, Kreuzungen, Plätze, Parkplätze, Brücken: der **begehbare Boden** | **Mechs laufen nur auf Tiles dieser Palette.** Das Straßennetz muss zusammenhängen |
| `ruins` | Trümmer, Krater, Schutt, ausgebrannte Ruinen, Brandflecken, verwilderte Parks | frei |
| `buildings` | intakte und halb zerstörte Häuser, Dächer, Hochhäuser, Lagerhäuser, Fabriken, Schornsteine | frei |
| `fixed_targets` | Bodengeschütze | **exakt die Palette von Level 1** wie bisher |

- Hintergrund: eine Stadt mit Straßenschluchten, **teils intakte, teils zerstörte Gebäude** (eingestürzte Dächer,
  Löcher, Brandspuren, umgeknickte Laternen, Autowracks).
- Animationen (`animations.json`, bis 8 Animationen, 24 animierte Tiles): **Feuer** in Ruinen, **Rauch** aus
  Schornsteinen, **blinkende Warnlichter** auf Hochhäusern, **flackernde Leuchtreklame**. Optional `"cycle"` für ein
  Glühen (z. B. Feuerschein in `ruins`, 3–6 Farben).

## Teil B: zerstörbare Gebäude

Format wie Level 3. **Lagerhäuser und Fabriken** stehen eingestreut und sind zerstörbar (höchstens 48 zerstörte
Tiles): Lagerhaus und Fabrikhalle (`hall`, Feld für Feld), Fabrik mit Schornstein (`bunker`), Tanklager (`fuel`),
Container/Paletten (`crates`, `depot`), Funkturm/Radar (`radar`), Kontrollposten (`checkpoint`), Hangar (`hangar`).

## Teil C: Karte `levels/level4.json`

Wie Level 3: `"tileset"` und `"ground_targets"` = `"assets/art/level4/generated"`, 21 Tiles pro Zeile, etwa
**375 Zeilen**, höchstens 256 verschiedene Zeilen. Abschnitte als Vorschlag: zerstörte Vorstadt (0–95),
Industriegebiet mit Fabriken (96–183), Innenstadt mit Hochhäusern (184–279), Kommandozentrale/Festung (280–374).

- **Straßen** mindestens 2 Tiles breit und durchgehend verbunden (Mechs laufen dort), regelmäßig auch quer.
- `events`: `shop` (`mid`, etwa Zeile 188), `boss` (Zeile 352) vor einem **großen freien Platz** (etwa 16 Zeilen
  Straße/Platz ohne hohe Gebäude), `shop` (`end`, 368), `end` (375). **Keine** Panzer; Bodengeschütze optional auf
  Dächern und Plätzen.

## Teil D: Gegner (eigener Satz für Level 4)

Format wie `assets/art/enemies-level3/generated/` (`indexed-source.json`, `palettes.json`, `placement.json`,
Vorschauen 4× auf hellem und dunklem Untergrund). Größen und Anzahl sind **fest**:

| `group` | Gegner | `pose` | `phase` | Größe | Palette |
|---|---|---|---|---|---|
| `jet` | moderner Kampfjet, Deltaflügel oder Stealth-Form, kantig | 8 Richtungen (`north` … `northwest`) | 0–2 (Triebwerksglühen) | 16×16 | `air` |
| `attack_heli` | Kampfhubschrauber, schmal, Stummelflügel mit Raketen | 8 Richtungen | 0–2 (Rotor) | 16×16 | `heli` |
| `drone` | Quadrocopter-Drohne, X-Rahmen mit vier Rotoren, Sensorkopf | `straight`, `left`, `right` (geneigt) | 0–2 (Rotoren) | 16×16 | `drone` |
| `mech` | kleiner zweibeiniger Mech, Geschütz am Arm | `north`, `east`, `south`, `west` | 0–3 (Laufzyklus: Beine wechseln) | 16×16 | `mechs` |
| `walker` | schwerer vierbeiniger Läufer, Front unten, Geschützsockel oben | `south` | 0–1 (Schritt) | 32×32 | `mechs` |
| `walker` | Wrack des Läufers | `destroyed` | 0 | 32×32 | `mechs` |

- Auf den `walker` setzt das Spiel ein drehbares Geschütz; in `placement.json` angeben: `{"walker": {"guns": [[x, y]]}}`.
- Paletten: `air`, `heli`, `drone`, `mechs` (je 16 × [R,G,B]). Kräftige, unterschiedliche Farben je Typ
  (z. B. Jet dunkelgrau mit roten Akzenten, Hubschrauber dunkelgrün/sand, Drohnen weiß/orange mit cyan Sensor,
  Mechs stahlblau mit gelben Warnstreifen).
- Schlanke, detaillierte Silhouetten, 1 px dunkle Kontur, keine gedrehten Bilder (jede Richtung von Hand).
- Speicher: Flugzeuge, Drohnen und Läufer zusammen höchstens 324 Glyphen, die Mechs 48. Mit den Größen oben passt
  alles (202 und 48). Das Prüfskript rechnet nach.

## Teil E: Endboss – großer Kampf-Mech

Format wie die bisherigen Bosse (`assets/art/boss-level3/generated/` als Vorlage), **eine** Palette (`palette.rgb`).
Ein **schwerer zweibeiniger Kampf-Mech**, Front zum Spieler (unten). Er **stapft** seitlich über den Platz (die Beine
bewegen sich nur beim Gehen), trägt vier Waffen, hat einen **Flammenwerfer-Arm** und lässt **Drohnen** von seinem
Rücken starten. Nach den vier Waffen öffnet sich die Brustpanzerung und gibt den Reaktor frei.

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body` | höchstens **112×64** | Rumpf mit Schultern, Hüfte und Cockpit, **ohne Beine**. Index 0 im Rumpf durchsichtig |
| `rotor_0`, `rotor_1`, `rotor_2` | je bis **32×48** | **ein Bein** in drei Schrittphasen (vorn, Mitte, hinten). Das Spiel setzt es links und rechts unter den Rumpf, gegenläufig |
| `turret_nw/ne/sw/se_south`, `…_southeast`, `…_destroyed` | je 16×16 | vier Waffen: Raketenwerfer auf den Schultern, Kanonen an den Armen |
| `core_exposed` | 32×32 | geöffnete Brustpanzerung mit glühendem Reaktor |
| `muzzle_0`, `muzzle_1` | je 16×16 | Mündungsfeuer |
| `flame_0`, `flame_1`, `flame_2` | je **16×32** | Flammenstrahl des Arms nach unten: kurz, voll, ausklingend (wie beim Hover-Panzer) |
| `spray_0`, `spray_1`, `spray_2` | je **32×16** | Staub, Funken und Trümmer an den Füßen beim Aufstampfen |
| `deck_jet_0`, `deck_jet_1`, `deck_jet_2` | je **16×16** | Drohne startet vom Rücken: angedockt, abhebend, im Flug (Front nach unten) |

`placement.json` wie beim Hover-Panzer und Träger:

```json
{
  "body": "body", "body_size": [112, 64], "palette": "boss",
  "turrets": [ … vier, mit offset, south, southeast, destroyed … ],
  "core": {"offset": [x, y], "size": [32, 32], "exposed_overlay": "core_exposed"},
  "rotors": [{"id": "leg_l", "offset": [x, y], "phase_offset": 0}, {"id": "leg_r", "offset": [x, y], "phase_offset": 1}],
  "rotor_frames": ["rotor_0", "rotor_1", "rotor_2"],
  "muzzle": {"frames": ["muzzle_0", "muzzle_1"], "south_offset_from_turret": [0, 15]},
  "flame": {"frames": ["flame_0", "flame_1", "flame_2"], "offset": [x, y]},
  "spray": {"frames": ["spray_0", "spray_1", "spray_2"], "offsets": [[x, y], [x, y]]},
  "catapult": {"frames": ["deck_jet_0", "deck_jet_1", "deck_jet_2"], "offset": [x, y]}
}
```

- Die Beine (`rotors`) hängen **unter** dem Rumpf: `offset` y etwa bei der Hüfte (darf bis Rumpfhöhe + 8 reichen).
  Rumpf + Beine zusammen höchstens etwa **112 px hoch**, damit unten Platz für den Spieler bleibt.
- `spray.offsets` an den Füßen (unter den Beinen), `flame.offset` an der Hand des Flammenwerfer-Arms.
- Speicher: höchstens **324 Glyphen**; mit Rumpf 112×64 und Beinen 32×48 etwa 237. Das Prüfskript rechnet nach.

## Checkliste für den Pull Request

- [ ] Basis-Branch `stage14`; nur neue Dateien in `assets/art/level4/`, `assets/art/enemies-level4/`,
      `assets/art/boss-level4/` und `levels/level4.json`
- [ ] `python3 tools/check_level4_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Tileset, ganzer Level, Animationen, Gebäude intakt/zerstört, alle Gegner in allen Richtungen und
      Phasen (4×), Boss zusammengesetzt (Waffen intakt/zerstört, Brust offen), Laufzyklus der Beine, Flamme, Staub,
      Drohnenstart
- [ ] Kurze Beschreibung: Abschnitte, Zuordnung Gebäude → `kind`, Animationen, Idee des Bosses
