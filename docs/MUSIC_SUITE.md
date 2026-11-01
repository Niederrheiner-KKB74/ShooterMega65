# Originalmusik für ShooterMega65

Vier neu komponierte, dreistimmige Stücke nach `docs/music_json.md` aus Stage 4,
Commit `5db5fa029668fc52b5f71082e5a64f713b4b1ac4`. Keine fremden Melodien oder Samples.
Die Spieldateien enthalten ausschließlich die dort beschriebenen JSON-Felder.

| Spieldatei | Länge | Tempo | Aufbau |
|---|---:|---|---|
| `music/level1.json` | 92,16 s, Loop 0 | 6 Frames/Zeile, 125 BPM | 48 Takte, e-Moll, treibendes Pulse-Motiv, Arpeggios, Bass/Drums |
| `music/shop.json` | 30,72 s, Loop 0 | 8 Frames/Zeile, 93,75 BPM | 12 Takte, G-Dur/e-Moll, Dreieck-Melodie, weiche Akkorde, kein Schlagzeug |
| `music/game_over.json` | 5,76 s, Ende | 6 Frames/Zeile, 125 BPM | 3 Takte, absteigendes Motiv, chromatischer Abschluss nach e-Moll |
| `music/level_clear.json` | 4,80 s, Ende | 5 Frames/Zeile, 150 BPM | 3 Takte, aufsteigende E-Dur-Fanfare mit Schlussakkord |

Alle Angaben gelten bei 50 Hz und vier Zeilen je Viertelnote. Der Shop wirkt
durch längere Noten, Pausen und geringere Lautstärke deutlich ruhiger.
Gesamtlautstärke: Level 14, Shop 10, Jingles 12 (jeweils von 15).

## Musikalischer Verlauf

Level: wiederkehrender E–G–B-Kopf, wechselnde Antworten, tiefere Mittelpassagen,
Rückkehr und Steigerung. 12 Vier-Takt-Abschnitte mit Em/C/G/D, Am und B-Dur als
Dominante. Das letzte B-Dur mit D# führt wieder ins eröffnende Em. Kein einmaliges
Intro und kein Fade-out: der gesamte Abschnitt ist die Schleife. Stimme 1 ist
die Melodie, Stimme 2 kurze Dur-/Moll-/Dominant-Arpeggios. Stimme 3 wechselt
zwischen Bass, Kick, Snare und Hi-Hat; es gibt nie mehr als drei gleichzeitige Stimmen.

Shop: drei Vier-Takt-Phrasen in der verwandten Dur-Tonart; langsame Melodie,
luftige Puls-Akkorde, Dreieck-Bass. Der letzte D-Dur-Takt führt nach G zurück.
Die Notenfreigaben liegen innerhalb des Taktrasters; am Loop wird keine Pause,
Überblendung oder zusätzliche Stille eingefügt. Der erste Ton jedes Patterns
nennt sein Instrument explizit, damit kein Zustand vom vorigen Durchlauf nötig ist.

Game Over: C-Dur → B-Dur → e-Moll, fallende Linie mit F–E als letzter Spannung.
Levelende: E-Dur → B-Dur → E-Dur, bewusst heller als die e-Moll-Levelmusik.
Beide Jingles haben `loop: null`, lösen alle Gates und lassen die Release-Tails
innerhalb ihrer Gesamtlänge ausklingen.

## Quellen, Prüfung und Hörproben

`tools/compose_music_suite.py` enthält die nachvollziehbare Partitur und schreibt
die vier JSON-Dateien deterministisch. Die JSONs sind eigenständig nutzbar;
der Generator wird zum Spielen nicht gebraucht.

```sh
python tools/compose_music_suite.py
python tools/validate_music_suite.py
python -m pip install -r tools/music-preview-requirements.txt
python tools/render_music_preview.py
python tools/check_music_suite.py
```

Python 3; die Validierung/Komposition benötigt nur die Standardbibliothek.
Die Hörproben benötigen NumPy 2.3.5. `previews/` wird lokal erzeugt; WAV-Dateien
liegen im Downloadpaket und werden wegen ihrer Größe nicht im Git-PR abgelegt.
Es entstehen vier vollständige WAVs und je ein 8-Sekunden-Ausschnitt über den
echten Übergang der beiden Schleifen (`*_loop_check.wav`: letzte 4 + erste 4 s).
Format: Mono, 22050 Hz, PCM 16 Bit, gleicher Render-Gain über alle Stücke.

**Die Hörproben sind eine einfache SID-inspirierte Synthese, kein SID-Emulator.**
Puls/Sägezahn/Dreieck/Rauschen, Hüllkurven, Arpeggios, Vibrato und Wavetables
werden angenähert. Analoge SID-Modelle, exakte ADSR/Gate-Details, Filter und
Hardware-Timing sind nicht simuliert. Es wird kein Filter benötigt. Der letzte
Wavetable-Eintrag bleibt stehen, wie spezifiziert. Oszillatorphase/Noise werden
für die Vorschau deterministisch behandelt; das ist keine Hardware-Klangreferenz.

Geprüft: erlaubte Felder, Werte, Noten und Instrumentreferenzen, Pattern-/Order-
Limits, gleich viele Zeilen aller drei Stimmen, ausgerichteter Loop-Einstieg,
Längen, Gate-Freigaben und absichtlich fehlerhafte Eingaben. Level: 36 Patterns,
8 Instrumente; Shop: 9/4; Jingles: je 3/4. Die WAVs clippen nicht und ihre
Schleifen-Samplegrenzen springen nicht. Komposition und Rendering sind reproduzierbar.
Berichte: `music-validation.json` und `music-preview-report.json` neben diesem Dokument.

Der angekündigte offizielle `tools/build_music.py` und ein Musik-Abspieler sind
in der geprüften Stage-4-Basis noch nicht enthalten. Deshalb wurden die Stücke
**mit der eigenen Spezifikationsprüfung geprüft, nicht mit dem künftigen
Spiel-Konverter kompiliert**. Keine Änderungen an Spielcode, SFX, Speicherbelegung
oder alten Releases. Nicht im Emulator oder auf MEGA65-Hardware gehört.
Nach Einbindung prüfen: Tempo 50 Hz, Instrumentwechsel, Loop-Sprung, Release-Tails,
Shop-Wechsel und Zusammenklang mit den auf einem anderen SID laufenden Effekten.
