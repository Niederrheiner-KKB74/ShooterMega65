# Musikformat (JSON) – Anleitung für Musik mit ChatGPT

Musik für ShooterMega65 wird als **JSON-Textdatei** geschrieben, nicht als SID-, PRG- oder MIDI-Datei.
Ein Konverter (`tools/build_music.py`) prüft die Datei, meldet Fehler mit Pattern und
Zeile und erzeugt daraus die Daten für den Abspieler im Spiel. Der Abspieler läuft 50-mal pro Sekunde (PAL).

## Klangrahmen
- Die MEGA65 hat vier SID-Chips. **Die Musik bekommt einen SID mit drei Stimmen**, die Soundeffekte einen anderen.
  Jede Stimme spielt immer nur einen Ton gleichzeitig. Akkorde entstehen durch Arpeggio oder Aufteilung auf Stimmen.
- Pro Stimme: Wellenform (Dreieck, Sägezahn, Rechteck, Rauschen), Hüllkurve (ADSR), Pulsbreite.
  Ein gemeinsamer Filter pro SID.
- Notenbereich `C-0` bis `B-7`.
- Gute Aufteilung: Stimme 1 Melodie, Stimme 2 Begleitung/Arpeggio, Stimme 3 Bass und Schlagzeug im Wechsel.

## Gewünschte Stücke
| Name | Länge | Hinweis |
|---|---|---|
| `level1` | Schleife 60–120 s | Levelmusik, treibend; muss nahtlos von vorn beginnen (Level dauert 4 Minuten) |
| `shop` | Schleife 20–40 s | ruhiger, während der Shop offen ist |
| `game_over` | 3–8 s, keine Schleife | kurzer Abschluss |
| `level_clear` | 3–8 s, keine Schleife | für das Levelende (später) |

Jedes Stück ist eine eigene Datei: `music/level1.json`, `music/shop.json` usw.

## Aufbau
```json
{
  "format": "shootermega65-music-1",
  "name": "Level 1 – Coastal Assault",
  "tempo": 6,
  "volume": 15,
  "filter": {"mode": "lowpass", "cutoff": 1200, "resonance": 6},
  "instruments": { … },
  "patterns": { … },
  "order": {
    "voice1": ["intro_m", "a_m", "a_m", "b_m"],
    "voice2": ["intro_h", "a_h", "a_h", "b_h"],
    "voice3": ["intro_b", "a_b", "a_b", "b_b"]
  },
  "loop": 1
}
```

| Feld | Bedeutung |
|---|---|
| `tempo` | Frames pro Patternzeile (3–31). 6 Frames = 0,12 s pro Zeile; mit 4 Zeilen pro Schlag sind das 125 BPM. Zwei Frames vor jeder neuen Note schaltet der Abspieler den Ton kurz ab (Hard Restart), damit die Hüllkurve sauber neu startet. |
| `volume` | Gesamtlautstärke 0–15 (Standard 15). |
| `filter` | Optional: `mode` `lowpass`/`bandpass`/`highpass`, `cutoff` 0–2047, `resonance` 0–15. Welche Stimmen gefiltert werden, steht beim Instrument. Filter sparsam einsetzen, er klingt je nach SID-Modell unterschiedlich. |
| `order` | Reihenfolge der Patterns, **für jede Stimme eine eigene Liste**. Alle drei Listen müssen zusammen gleich viele Zeilen ergeben, sonst laufen die Stimmen auseinander (der Konverter prüft das). |
| `loop` | Index in den `order`-Listen, an dem nach dem Ende weitergespielt wird (0 = ganz von vorn). `null` = Stück endet (Jingles). |

## `instruments`
```json
"instruments": {
  "lead":  {"wave": "pulse", "attack": 0, "decay": 8, "sustain": 10, "release": 6,
            "pulse": 1024, "pulse_sweep": 24, "vibrato": {"delay": 12, "speed": 3, "depth": 3}},
  "chord": {"wave": "saw", "attack": 0, "decay": 6, "sustain": 6, "release": 4, "arpeggio": [0, 4, 7]},
  "bass":  {"wave": "pulse", "attack": 0, "decay": 9, "sustain": 0, "release": 2, "pulse": 2048, "filter": true},
  "kick":  {"attack": 0, "decay": 8, "sustain": 0, "release": 0,
            "wave_table": [["pulse", 12], ["triangle", 0], ["triangle", -5], ["triangle", -10], ["triangle", -14]]},
  "snare": {"attack": 0, "decay": 9, "sustain": 0, "release": 0,
            "wave_table": [["noise", "C-7"], ["pulse", 0], ["noise", "A-6"], ["noise", "F-6"]]},
  "hihat": {"attack": 0, "decay": 4, "sustain": 0, "release": 0, "wave_table": [["noise", "C-7"]]}
}
```

| Feld | Bedeutung |
|---|---|
| `wave` | `triangle`, `saw`, `pulse`, `noise` |
| `attack`, `decay`, `sustain`, `release` | SID-Hüllkurve, je 0–15 (Werte wie im C64-Handbuch) |
| `pulse` | Pulsbreite 0–4095 (2048 = Rechteck 50 %), nur für `pulse` |
| `pulse_sweep` | Änderung der Pulsbreite pro Frame (−255 … 255); läuft zwischen 256 und 3840 hin und her |
| `vibrato` | `delay` Frames bis zum Einsatz, `speed` Frames pro Viertelschwingung (1–15), `depth` in Achtel-Halbtönen (1–15) |
| `arpeggio` | Halbtonabstände, die Frame für Frame reihum gespielt werden, z. B. `[0, 4, 7]` = Dur-Akkord |
| `wave_table` | Für Schlagzeug und Effekte: ein Eintrag pro Frame, `[Wellenform, Ton]`. Ton ist ein Halbtonabstand zur gespielten Note (Zahl) oder eine feste Note (`"C-7"`). Der letzte Eintrag bleibt stehen. Ersetzt `wave` und `arpeggio`. |
| `filter` | `true` = diese Stimme läuft durch den Filter |

Höchstens 32 Instrumente pro Stück.

## `patterns`
Ein Pattern ist eine Liste von Zeilen für **eine** Stimme, 1–64 Zeilen. Jede Zeile ist ein Text:

| Zeile | Bedeutung |
|---|---|
| `"C-4 lead"` | Note C in Oktave 4 mit Instrument `lead` anschlagen (Kreuz: `"C#4"`, nur Kreuze, keine Bs) |
| `"E-4"` | Note mit dem zuletzt benutzten Instrument dieser Stimme anschlagen |
| `"..."` | nichts ändern, der Ton klingt weiter |
| `"off"` | Ton loslassen (Hüllkurve geht in den Release) |
| `"C-4 lead >"` | wie oben, aber **gebunden**: die Tonhöhe wechselt ohne neuen Anschlag (Legato) |

```json
"patterns": {
  "a_m": ["C-5 lead", "...", "...", "...", "D#5", "...", "G-5", "...",
          "F-5", "...", "D#5", "...", "D-5", "...", "off", "..."],
  "a_b": ["C-2 bass", "...", "C-2 snare", "...", "C-2 bass", "C-3 bass", "C-2 snare", "...",
          "G#1 bass", "...", "C-2 snare", "...", "A#1 bass", "...", "C-2 snare", "C-2 hihat"]
}
```

Bei `wave_table`-Instrumenten (Schlagzeug) bestimmt die Note nur Tonhöhen mit Zahlenabstand, feste Noten bleiben fest.

Höchstens 128 Patterns pro Stück, höchstens 128 Einträge pro `order`-Liste.

## Soundeffekte
Die Effekte (Schüsse, Explosionen, Kapsel aufsammeln, Kauf im Shop, Bombe, Unverwundbarkeit, Rakete) laufen auf
einem eigenen SID und unterbrechen die Musik nicht. Sie stehen in `music/sfx.json`; die Namen der Effekte sind
fest, weil das Spiel sie aufruft (`shot`, `missile`, `cursor`, `select`, `hit`, `explode`, `explode_big`,
`player_hit`, `player_dead`, `bomb`, `coin`, `shield`, `invulnerable`, `buy`). Ein Effekt besteht aus:

| Feld | Bedeutung |
|---|---|
| `voice` | Effektstimme 0–2. Schüsse/Rakete/Shop-Cursor 0, Explosionen/Bombe 1, Treffer/Kapseln/Kauf 2 |
| `priority` | 1–255. Ein Effekt unterbricht einen noch klingenden Effekt derselben Stimme nur bei gleicher oder höherer Priorität |
| `note` | Grundton für Zahlenabstände in der `wave_table` |
| `frames` | Frames bis zum Loslassen (Release), Standard = Länge der `wave_table` |
| `attack` … `release`, `pulse`, `wave_table` | wie bei den Instrumenten |

Beispiel:

```json
{"format": "shootermega65-sfx-1",
 "sfx": {"explosion_small": {"note": "C-3", "attack": 0, "decay": 10, "sustain": 0, "release": 0,
                              "wave_table": [["noise", "C-5"], ["noise", "G-4"], ["noise", "C-4"], ["noise", "G-3"]]}}}
```

## Hinweise für ChatGPT
- Nur die oben beschriebenen Felder verwenden; unbekannte Felder sind ein Fehler.
- Jede `order`-Liste muss dieselbe Gesamtzahl an Zeilen ergeben.
- Für eine Schleife von 90 s bei `tempo` 6 braucht man etwa 750 Zeilen, also z. B. zwölf Patterns zu 64 Zeilen pro
  Stimme. Wiederholungen über `order` sparen Platz.
- Bitte eine kurze Beschreibung des Stücks (Tonart, Tempo, Aufbau) beilegen, und zum Probehören ein Rendering
  als WAV oder MP3, falls das möglich ist. Das Spiel verwendet nur die JSON-Datei.
