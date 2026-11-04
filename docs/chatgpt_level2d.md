# Auftrag an ChatGPT: neuer Boss für Level 2 – Hover-Panzer

**Basis-Branch ist `stage10`.** Bitte den Pull Request gegen `stage10` stellen und nur `assets/art/boss-level2/`
ändern. Allgemeine Regeln (Pixelgenauigkeit, Palettenindizes, Draufsicht, Licht von oben links) wie in
`docs/chatgpt_level2.md`.

## Warum ein neuer Boss

Der Landkreuzer musste sich als Kettenfahrzeug vor jedem Richtungswechsel drehen. Die 45°-Ansicht passte nur
verkleinert in den Speicher, dadurch schien er beim Drehen zu schrumpfen. Der neue Boss braucht **keine Drehung**:
ein **schwerer Hover-Panzer** (Luftkissenfahrzeug) der Raffinerie-Wache, der auf seiner Schürze in jede Richtung
gleitet. Er ersetzt den Landkreuzer vollständig.

## Idee und Spielablauf

- Draufsicht, Front nach unten (zum Spieler). Breiter, flacher Rumpf mit umlaufender Gummischürze, zwei große
  Hubgebläse (Lüfter) im Heck oder an den Seiten, schwere Panzerplatten in Wüstentarnung, Abgas-Auslässe.
- Er gleitet seitlich und auf und ab über den Platz vor der Raffinerie, ohne sich zu drehen.
- **Vier Waffentürme** wie bisher: müssen zuerst zerstört werden.
- **Schwachpunkt**: danach öffnet sich eine Klappe über dem Reaktor/Gebläsemotor (`core_exposed`).
- **Neu: Flammenwerfer** an der Front. In der Endphase stößt er immer wieder einen kurzen Flammenstrahl nach unten
  aus, der dem Spieler schadet, wenn er hineinfliegt.
- **Neu: aufgewirbelter Staub** am Rand der Schürze, solange er gleitet.

## Frames (`assets/art/boss-level2/generated/indexed-source.json`)

Format wie bisher: Liste von Frames mit `id`, `width`, `height`, `rows` (**zwei Hex-Ziffern pro Pixel**),
Breite Vielfaches von 16, Höhe Vielfaches von 8. Index 0 ist durchsichtig.

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body` | höchstens **128×80**, empfohlen 112×80 | Rumpf mit Schürze, Front unten. Geschlossen, Index 0 im Rumpf ist durchsichtig |
| `turret_nw/ne/sw/se_south`, `…_southeast`, `…_destroyed` | je 16×16 | vier Türme: Rohr Süden, Südosten (Südwesten spiegelt das Spiel), zerstört |
| `core_exposed` | 32×32 | die geöffnete Klappe mit glühendem Motor/Reaktor |
| `rotor_0`, `rotor_1`, `rotor_2` | je bis 32×32 | drei Phasen der Hubgebläse (drehende Lüfterblätter). Das Spiel setzt sie an bis zu 4 Stellen ein |
| `muzzle_0`, `muzzle_1` | je 16×16 | Mündungsfeuer der Türme |
| `flame_0`, `flame_1`, `flame_2` | je **16×32** | Flammenstrahl nach unten: kurz/aufflackernd, voll, ausklingend. Heller Kern, orange/rot nach außen, an den Rändern durchsichtig |
| `spray_0`, `spray_1`, `spray_2` | je **32×16** | aufgewirbelter Staub und Sand am Schürzenrand, drei Phasen, locker und an den Rändern durchsichtig. Grau-beige, damit er auf Sand und auf Beton passt |

Die Frames des Landkreuzers, die es nicht mehr gibt, bitte entfernen: `body_side`, `core_exposed_side`,
`rotor_side_0`–`2`, `body_diag`, `core_exposed_diag`, `dust_0`, `dust_1`.

## Palette

**Eine** Palette mit 15 Farben plus Durchsichtig (`palette.rgb`, 48 Byte) für den ganzen Boss, auch für Flammen und
Staub. Ein heller Treffer-Blitz wird automatisch daraus erzeugt. Für die Flamme werden Gelb-, Orange- und Rottöne
gebraucht, für den Staub zwei bis drei Grau-Beige-Töne. Die Tarnfarben des Rumpfs bitte damit abstimmen.

## Positionen (`placement.json`)

Wie bisher, ohne `side` und `diag`:

```json
{
  "body": "body", "body_size": [112, 80], "palette": "boss",
  "turrets": [{"id": "turret_nw", "offset": [x, y], "size": [16, 16], "south": "turret_nw_south",
               "southeast": "turret_nw_southeast", "destroyed": "turret_nw_destroyed"}, … vier …],
  "core": {"offset": [x, y], "size": [32, 32], "exposed_overlay": "core_exposed"},
  "rotors": [{"id": "fan_l", "offset": [x, y], "phase_offset": 0}, … bis zu vier …],
  "rotor_frames": ["rotor_0", "rotor_1", "rotor_2"],
  "muzzle": {"frames": ["muzzle_0", "muzzle_1"], "south_offset_from_turret": [0, 15]},
  "flame": {"frames": ["flame_0", "flame_1", "flame_2"], "offset": [x, y]},
  "spray": {"frames": ["spray_0", "spray_1", "spray_2"], "offsets": [[x, y], [x, y], …]}
}
```

- `offset` ist jeweils die linke obere Ecke relativ zur linken oberen Ecke des Rumpfs.
- `flame.offset`: wo das 16×32-Flammenbild sitzt. Die Düse ist an der Front unten, die Flamme darf über den Rumpf
  hinaus nach unten ragen.
- `spray.offsets`: 2 bis 4 Stellen am Schürzenrand (links, rechts, hinten), auch teilweise außerhalb des Rumpfs.

## Speicher

Für den Boss stehen **324 Glyphen** zur Verfügung. Ein Frame kostet Breite/16 × (Höhe/8 + 1) Glyphen, dazu kommt 1;
Südost-Ansichten zählen doppelt. Das Spiel legt manche Frames so groß an wie beim Boss von Level 1 (Rumpf mindestens
96×64, `core_exposed` und Rotoren 32×32). Beispiel mit Rumpf 112×80: Rumpf 77, Türme 48, Motorraum 10, Rotoren 30,
Mündungsfeuer 6, Flammen 15, Staub 18, plus 1 = 205. Es bleibt also reichlich Luft. Das Prüfskript rechnet nach.

## Checkliste für den Pull Request

- [ ] Basis-Branch `stage10`; nur `assets/art/boss-level2/` geändert
- [ ] `python3 tools/check_level2_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Boss zusammengesetzt (Türme intakt und zerstört, Klappe offen), Lüfter-Animation, Flammenstrahl
      (alle drei Phasen an der Düse), Staub an der Schürze
- [ ] Kurze Beschreibung des Designs
