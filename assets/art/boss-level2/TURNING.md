# Drehung des Landkreuzers

Die neue 96×96-Ansicht zeigt die Front nach unten links. Polygongeometrie,
diagonale Kettenglieder und Panzerung werden im Zielraster gezeichnet.
Kantenlichter werden im Bildschirmkoordinatensystem oben links gesetzt.
Vier Türme verwenden die vorhandenen Geschützbilder auf den neuen Sockeln.

`placement.json` enthält die neue Anordnung unter `diag`, einschließlich
Motorraum und vier Staubpositionen. Zwei 16×16-Staubphasen verwenden
Sand-/Grautöne mit transparenten Zwischenräumen und Außenrändern.

Die gemeinsame Speicherbelegung mit den Framegrößen des Level-1-Bosses beträgt
323 von 324 Glyphen. Der diagonale Rumpf benötigt 78 Glyphen, der Motorraum 10
und die beiden Staubphasen zusammen 6.

Aus dem Repository-Stamm:

```sh
python assets/art/boss-level2/source/generate_turn.py
python tools/check_level2_art.py
```

Der Generator ergänzt die vier neuen Frames und `diag` in den vorhandenen
Dateien. `boss-turn-preview.png` zeigt die drei Ansichten mit den Türmen.
`boss-turn-animation.gif` zeigt den Wechsel in beide Richtungen.
`dust-preview.png` vergrößert beide Staubphasen.

Geprüft sind das Datenformat, Speicherbudget, die Erhaltung aller bestehenden
Frames, bytegleiche Reproduktion und der geschlossene diagonale Rumpf.
Die Spielintegration und Hardwareprüfung folgen.
