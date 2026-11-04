# Hover-Panzer der Raffinerie-Wache

112×80-Pixel-Rumpf mit umlaufender Gummischürze, zwei 32×32-Hecklüftern,
vier separaten 16×16-Türmen und einer gepanzerten Reaktorklappe.
Die Front zeigt nach unten. Breite Sandtarnflächen, dunkle Schürzenfalten,
Stahlgitter, Wartungsluken und rote Rückleuchten gliedern die Draufsicht.

Die Palette enthält einen transparenten Eintrag und 15 gemeinsame Farben.
Dunkles Gummi und Stahl, Sand-/Beigetöne sowie Rot, Orange, Gelb und
helles Cremeweiß tragen Rumpf, Staub, Mündungsfeuer und Flammenstrahl.

## Dateien und Vorschauen

- `generated/indexed-source.json` enthält alle 25 Frames mit zwei Hex-Ziffern je Pixel.
- `generated/placement.json` legt vier Türme, Reaktorklappe, zwei Lüfter,
  die Frontdüse und vier Staubpositionen fest.
- `generated/palette.rgb` enthält 16 × RGB, 48 Byte.
- `generated/boss-preview.png` zeigt aktive Türme und die Endphase.
- `generated/boss-animation.png` zeigt Lüfter und gleitenden Staub als APNG.
- `generated/boss-flame-animation.png` animiert die Endphase mit drei Flammenphasen.
- `generated/flame-phases.png` zeigt alle drei Flammenphasen an derselben Düse.
- `generated/frame-sheet.png` zeigt den Rumpf 1× und die übrigen Frames 4×.

Die Flamme beginnt an `[48,77]` und reicht bis 32 Pixel nach unten.
Die Effekte haben transparente Außenbereiche. Die beiden Lüfter haben
versetzte Phasen. Der Motorraum wird bei `[40,35]` eingeblendet.
Waffenverhalten, Trefferpunkte und Effektzeiten konfiguriert das Spiel.

## Reproduktion und Prüfung

Aus dem Repository-Stamm mit Python 3 und Pillow:

```sh
python assets/art/boss-level2/source/generate_hover.py
python assets/art/boss-level2/source/verify_hover.py
python tools/check_level2_art.py
```

Die Prüfung des Level-Konverters benötigt zusätzlich NumPy.
Die Quellen sind native indexierte Pixelgeometrie mit Licht von oben links.
Erneutes Generieren erzeugt bytegleiche Dateien.
Die Zusatzprüfung kontrolliert den geschlossenen Rumpf, die 25 Frame-IDs,
die Palette, Effekttransparenz und Montagepunkte.

Gemeinsame Glyphbelegung gemäß Repository-Checker einschließlich der
Mindestgrößen des Level-1-Bosses: **205 von 324 Glyphen**.
Die vollständige Checker-Ausgabe liegt in `validation/check_level2_art.txt`.
Der Kartenhinweis betrifft die bestehende Karte mit automatisch gesetzten Palmen.

Spielintegration und Hardwaretest stehen aus.
