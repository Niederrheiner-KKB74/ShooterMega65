# Auftrag an ChatGPT: Level 4 „Operation Iron City“ – Überarbeitung der Grafik

Level 4 läuft im Spiel (Stage 14). Der Besitzer hat es angesehen: **Die Gegner wirken im Vergleich zu Level 1 simpel
und wenig detailliert**, und **bei der Hintergrundgrafik ist schwer zu erkennen, was sie darstellen soll.** Der Boss
(Kampf-Mech) ist gut und bleibt.

**Basis-Branch ist `stage14`.** Bitte einen neuen Pull Request gegen `stage14` stellen und nur ändern:
`assets/art/level4/`, `assets/art/enemies-level4/` und in `levels/level4.json` **nur die Karte** (`map`).
`events`, `paths` und `formations` bitte nicht anfassen. Formate und Grenzen wie in `docs/chatgpt_level4.md`.
Prüfen mit `python3 tools/check_level4_art.py` (Ausgabe in die PR-Beschreibung).

## 1. Gegner: Detailgrad wie Level 1

Maßstab sind die Gegner aus Level 1: `assets/art/enemy-views/generated/fighter-preview.png`, `bomber-preview.png`,
`helicopter-preview.png` und die Panzer in `assets/art/ground-vehicles/generated/tank_atlas.png`. Bitte vor dem Zeichnen ansehen und vergleichen.

- **Plastische Schattierung** statt flacher Flächen: jede Fläche mit 2–3 Helligkeitsstufen (Licht von oben links,
  hellere Kanten oben/links, Schatten unten/rechts), 1 px dunkle Kontur.
- **Erkennbare Einzelteile**: Cockpitglas mit Glanzpunkt, Lufteinlässe, Leitwerke, Triebwerksdüsen mit Glühen,
  Waffen unter den Flügeln, Kennzeichen/Warnstreifen, Panzerplatten-Fugen.
- **Silhouette** muss auch klein sofort lesbar sein; die Fläche des 16×16-Rahmens gut nutzen (etwa 14×14), nicht
  zu dünn und nicht klumpig.
- Einzeln:
  - `jet`: moderner Kampfjet (Delta- oder Doppelleitwerk), deutlich gepfeilte Flügel, zwei Triebwerke mit
    Glühen in drei Phasen, kantige Rumpfnase.
  - `attack_heli`: schmaler Rumpf mit Tandem-Cockpit, Stummelflügel mit Raketenbehältern, Heckrotor sichtbar,
    Hauptrotor in drei Winkelphasen als helle dünne Linien.
  - `drone`: X-Rahmen mit vier **deutlich sichtbaren** Rotorscheiben (hell, halbtransparent wirkend durch helles
    Gitter), Mittelkörper mit Sensorkopf und Lampe; die Neigung `left`/`right` an verkürzten Armen erkennbar.
  - `mech`: in Draufsicht von leicht schräg: **Rumpf mit Cockpit, zwei Schultern, Waffenarm, zwei Beine**, die im
    Laufzyklus deutlich abwechselnd vor- und zurückgehen (4 Phasen); in jeder Richtung klar, wohin er läuft.
  - `walker`: Panzerung mit Fugen, vier Beine mit Gelenken, Schrittphasen; Wrack mit Rauch/Feuer.
- Farben weiter je Typ unterschiedlich und kräftig; auf dunklem Asphalt und auf hellen Dächern gut sichtbar.

## 2. Hintergrund: als Stadt lesbar machen

Im Moment bestehen die Blöcke zwischen den Straßen überwiegend aus sich wiederholenden Kreisen, Kringeln und
braunen Kacheln. Man erkennt nicht, ob es Dächer, Ruinen oder Gelände sind. Bitte so gestalten, dass man auf einen
Blick eine (teilweise zerstörte) Stadt von oben sieht:

- **Gebäude als Gebäude**: deutliche **Dachflächen** mit Rand (Attika), Dachaufbauten (Lüftung, Klimageräte,
  Treppenhaus, Oberlichter, Antennen, Wassertanks), dazu an der **Südseite eine sichtbare Fassade** als schmaler
  Streifen mit Fensterreihen (leicht schräg von Süden gesehen) und ein **Schlagschatten** nach rechts unten auf
  Straße oder Hof. Verschiedene Gebäudetypen und Dachfarben (Beton hell, Teerpappe dunkel, Ziegel rot, Glas blau).
- **Zerstörte Gebäude** klar als solche: eingestürztes Dach mit sichtbaren Trägern, Löcher, Brandspuren,
  **Schuttkegel**, die auf die Straße ragen; nicht nur gemusterte Fläche.
- **Straßen**: Gehwege mit Bordsteinkante, Fahrbahnmarkierungen, Zebrastreifen, Laternen, Autowracks, Schlaglöcher
  und Krater. Kreuzungen deutlich.
- **Freiflächen**: Parks mit Bäumen, Plätze, Parkplätze, Baulücken mit Trümmern.
- **Weniger Rauschen**: große Flächen aus ruhigen Tiles mit wenigen Details; Kringel- und Punktmuster nur sparsam.
  Der Kontrast Dach – Straße – Schutt muss klar sein.
- Lagerhäuser und Fabriken (zerstörbar) als größere, eindeutige Gebäude mit Sheddach, Schornstein, Ladetoren.
- Animationen wie bisher (Feuer, Rauch, Warnlichter, Leuchtreklame), gern gut sichtbar an den Gebäuden.
- Höchstens **126 Tiles** einschließlich Animationsphasen, höchstens 48 zerstörte Tiles, Straßen in der Palette
  `streets` durchgehend verbunden (die Mechs laufen nur dort), freier Platz vor dem Boss (Zeile 352) bleibt.

## Checkliste

- [ ] Basis-Branch `stage14`; nur die genannten Ordner und die `map` geändert
- [ ] `python3 tools/check_level4_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: alle Gegner 4× **neben den Level-1-Gegnern zum Vergleich**, Tileset, ganzer Level und ein
      Ausschnitt in Originalgröße (320×200) aus jedem Abschnitt
