# Leveldaten: Recherche und Formatvorschlag

Stand 01.11.2026. Teil 1 fasst zusammen, wie Spiele der 8-/16-Bit-Ära Levelaufbau und Gegnerangriffe
gespeichert haben. Teil 2 leitet daraus ein Format für ShooterMega65 ab. Die Leveldaten liegen dabei in
eigenen Dateien und nicht im Programm. Quellen stehen am Ende.

## Teil 1 – Wie es damals gemacht wurde

### 1.1 Hintergrund: Hierarchie statt Einzelzeichen
Fast alle Spiele speichern die Karte nicht Zeichen für Zeichen, sondern in mehreren Ebenen. Jede Ebene wird
mit 1 Byte adressiert:

| Ebene | Typische Größe | Beispiele |
|---|---|---|
| Zeichen (char) | 8×8 | C64: höchstens 256 gleichzeitig |
| Tile / Metatile | 16×16 (2×2 Zeichen) | NES-Standard; C64-Spiele mit 2×2-Blöcken |
| Metametatile / Chunk | 32×32 … 256×256 | *Mega Man* 32×32, *Blaster Master* 64×64, *Sonic 2* 128×128 |
| Spalten-/Zeilenvorlagen | ganze Spalte oder Zeile | *The Legend of Zelda* (Liste von Spaltenvorlagen), *Super Mario Bros.* (Spaltenvorlagen plus Objekte darauf) |
| Räume / Bildschirme | ein Bildschirm | *Metroid*: wiederverwendbare Räume, verkettet |

Größenordnung: Ein 32×32-Chunk braucht nur 25 % der Daten von 16×16-Tiles (plus ein kleines Wörterbuch).
Ein C64-Bildschirm mit 40×24 Zeichen (960 Byte) schrumpft mit 2×2-Tiles auf 240 Byte, mit Meta-Tiles noch
weiter. Auf diese Hierarchie wird oft noch allgemeine Kompression gesetzt, RLE oder LZ (z. B. *Kirby's Adventure*).
Das erlaubt freie Platzierung, packt aber schlechter als reine Strukturtricks. Auf C64/MEGA65 übliche
Packer sind Exomizer und ZX0; Vyper nutzt bereits einen ZX0-Streaming-Entpacker.

Weitere Kniffe:
- **Objektbasierte Karten** (*Super Mario Bros.*, *Super Mario World*): Der Level ist eine Liste von Befehlen
  „Objekt X an Position (x, y), Länge n“ mit 2–3 Byte pro Objekt. Ein Flag „nächste Seite“ ersetzt
  absolute Koordinaten.
- **Auto-Tiling** (*Nova the Squirrel*): Kanten und Übergänge berechnet das Spiel aus den Nachbarn, die Daten
  enthalten sie nicht.
- **Symmetrie und Spiegelung** (*Micro Mages*: 256×32 Pixel in 4 Byte).
- **Grafiksatz pro Level** (*Zanac*: ein gemeinsamer Teil plus ein Teil pro Gebietsgruppe, RLE-gepackt).

### 1.2 Gegner: Platzierungslisten nach Scrollposition
Bei Scrollern hängen die Gegner an der Levelposition und erscheinen bei jedem Durchlauf gleich.
Im Atari-Age-Forum wird das für *Armalyte* beschrieben: gleiche Wellen und Boni zu gleichen Zeitpunkten.
Mayhem-in-Monsterland-Entwickler: „the enemies are directly linked to the scrolling level“.
Das bestdokumentierte Beispiel ist *Super Mario Bros.*:

- Eine **eigene Gegnerliste** pro Bereich, getrennt von der Hintergrundliste.
- **2 Byte pro Eintrag**: `XXXXYYYY` / `PHCCCCCC`. Position relativ zur aktuellen „Seite“ in 16-Pixel-Schritten,
  `P` = weiter zur nächsten Seite, `H` = nur im schweren Modus, `C` = Gegnertyp (64 Typen).
- Sonderbefehle in derselben Liste, z. B. Bereichswechsel (3 Byte). Endmarke `$FF`.

Die Liste ist nach Position **sortiert**. Das Spiel hält einen Lesezeiger und arbeitet die Einträge ab, sobald
die Scrollposition sie erreicht. Pro Frame kostet das nur einen Vergleich.

### 1.3 Angriffe: Bewegungsbahnen als kleine Skriptsprache
Für die Bewegung der Gegner gibt es eine sehr gut dokumentierte Primärquelle: Dave Jones (später DMA Design)
beschreibt in „The whole truth about Games Programming“ die Gegnersteuerung von *Menace* (Amiga, 1988):

- **Pro Gegner ein Datensatz**: Position, Sprite, Geschwindigkeit, Animation, Modus-Bits, **Trefferzahl**
  (`$FF` = unzerstörbar), Lesezeiger in die Bahn, Schleifenzähler, Pausen- und Verfolgungszähler, sowie ein
  Feld „tötet andere Gegner mit“ (für Gegnergruppen und Endgegnerteile).
- **Bahnen** sind Listen von Koordinatenpaaren, wahlweise absolut oder relativ (Modusbit). Werte, die keine
  gültige Bildschirmkoordinate sein können (`$E0–$EF`), sind **Befehle**: Unterprogramm/Rücksprung (gemeinsame
  Bahnstücke), Schleife, Pause, Spieler verfolgen (Seek, mit Dauer), Rakete starten, Sprite, Geschwindigkeit
  oder Animation wechseln. Eine Endmarke beendet die Bahn.
- Alle Bahnen eines Levels lagen in einer eigenen Datei („paths.s – all the paths for Level One“).
- Der Endgegner von *Menace* besteht aus mehreren normalen Gegnern (Speicher sparen).

Andrew Braybrook (*Uridium 2*) ergänzt aus seinem Entwicklungstagebuch:
- **Gespiegelte Bahnen** werden über ein Flag erzeugt („upside-down mode“), nicht als zweiter Datensatz.
- Angriffsbahnen wurden aus dem C64-*Uridium* übernommen. Klügeres Verhalten wie Verfolgen, Zielen oder
  Lenkraketen ist Code, der über Parameter gesteuert wird.
- Daten werden blockweise nachgeladen („one load from disk to pull in a whole fleet“).

Bei *Galaga* steuert ebenfalls ein Befehlsverteiler mit Unterbefehlen die Gegner (Kreisen, Formation halten,
Sturzflug). Dort gibt es zusätzlich Regeln abhängig vom Zustand, z. B. Dauerangriff, wenn weniger als sechs
Gegner übrig sind.

### 1.4 Laden
Bei Diskettenspielen werden Leveldaten pro Level nachgeladen und entpackt. Vyper macht das bereits so: KERNAL-SEQ-Lader
(`SETBNK` vor `SETNAM`), ZX0-Streaming beim Laden, Daten nach `$40000+` (Stage 10a2: 454 KB → 172 KB auf der
Diskette).

### Zusammengefasst
1. Hintergrund: hierarchisch (Tile → Block/Zeile → Level) plus allgemeiner Packer.
2. Gegner: getrennte, nach Scrollposition sortierte Ereignisliste mit relativen Positionen (2–4 Byte).
3. Bewegung: wiederverwendbare Bahnen als Bytecode mit eingebetteten Befehlen. Formationen = gleiche Bahn mit
   Zeitversatz, Spiegelung per Flag.
4. Pro Level eigene Dateien, gepackt, beim Levelwechsel geladen.

## Teil 2 – Vorschlag für ShooterMega65

### 2.1 Dateien pro Level (auf der D81, ZX0-gepackt)
| Datei | Inhalt | Ziel im Speicher |
|---|---|---|
| `LnGFX` | Tile-Glyphen (NCM), 4 Landschaftspaletten, Metatile-Tabelle | `$40000`, Palette |
| `LnMAP` | Zeilenwörterbuch + Zeilenliste (siehe 2.2) | Bank 5 / Attic RAM |
| `LnSCR` | Ereignisliste, Formationen, Bahnen, feste Ziele, Boss-Skript | Bank 5 |
| `OBJGFX` | Gegner/Schüsse/Explosionen/Kapseln (für alle Level gleich, einmal geladen) | `$48000` |

Das Programm enthält dann nur noch Code und das HUD. Shops und Endgegner können eigene Dateien bekommen.
Den Lader übernehme ich aus Vyper (Stage 10a2/10a6: SEQ, ZX0-Streaming, Prüfsummen).

### 2.2 Karte: Metatiles + Zeilenwörterbuch
Unsere Karte ist 21 Metatiles (16×16) breit und scrollt nur vertikal. Daraus folgt ein einfaches,
gut packendes Format im Stil der Spaltenvorlagen von *Zelda*, hier als Zeilen:

- **Metatile-Tabelle** (bis 256 Einträge à 3 Byte): obere Glyphe, untere Glyphe, Palettenbank.
  Die Farbbytes pro Zelle entfallen, weil die Palette am Metatile hängt.
- **Zeilenwörterbuch**: jede unterschiedliche Metatile-Zeile einmal, 21 Byte pro Zeile.
- **Zeilenliste**: 1 Byte pro 16 Pixel Levelhöhe (Index ins Wörterbuch).

Rechnung für einen Level von 4 Minuten (25 px/s → 6.000 px = 375 Zeilen) mit 120 verschiedenen Zeilen:
120 × 21 + 375 = 2.895 Byte, plus ZX0 deutlich weniger. Das Beispiel aus PR #4 (32 Zeilen) braucht so 
etwa 700 Byte statt 2,6 KB. Der Decoder bleibt so einfach wie heute (eine neue Glyphenzeile alle 8 Pixel).

Zerstörbare feste Ziele (Bunker, Flak) stehen nicht in der Karte, sondern als Ereignis in der Skriptdatei
(2.3). Das Ereignis enthält: Position, Metatiles intakt/zerstört, Trefferpunkte, Beute. Beim Abschuss
werden die betroffenen Ringpuffer-Zeilen umgeschrieben.

### 2.3 Ereignisliste (sortiert nach Scrollposition)
Jeder Eintrag beginnt mit dem **Abstand zum vorigen Eintrag in Metatile-Zeilen** (wie das Seitenflag von
*Super Mario Bros.*, nur als Zähler), gefolgt von Typ und Parametern:

| Typ | Parameter | Bytes |
|---|---|---|
| Formation | Formations-Nr., x, Flags (gespiegelt, schwer) | 5 |
| Bodeneinheit | Art, Spalte, Richtung, Bahn-Nr. | 6 |
| Festes Ziel | Spalte, Metatile intakt/zerstört, Treffer, Beute | 7 |
| Scrolltempo | neue Geschwindigkeit (8.8) | 4 |
| Shop | Shop-Nr. (Mitte / Ende) | 3 |
| Boss | Boss-Nr. (Scrollen stoppt) | 3 |
| Levelende | – | 2 |

Laufzeit: Ein Zähler wird bei jeder neuen Metatile-Zeile (alle 32 Frames) verringert. Bei 0 werden alle
fälligen Einträge ausgeführt. Ein Level mit 200 Ereignissen braucht etwa 1 KB.

**Formationen** liegen in einer Tabelle: Gegnerart, Anzahl, Bahn-Nr., Zeitversatz zwischen den Mitgliedern,
Startpunkt, Formationsbeute. Gleiche Bahn mit Versatz ergibt die typischen „Schlangen“. Mit dem
Spiegel-Flag braucht eine von links kommende Welle keinen eigenen Datensatz.

### 2.4 Bahnen (Bytecode nach dem Menace-Prinzip)
Pro Schritt: `dx, dy` (vorzeichenbehaftet, in 1/4 Pixel pro Frame) und Dauer in Frames, also 3 Byte für ein
gerades Bahnstück. Befehle liegen im Bereich `$80–$8F` des ersten Bytes:

| Befehl | Bedeutung |
|---|---|
| `LOOP n` / `ENDLOOP` | Abschnitt wiederholen |
| `CALL p` / `RET` | gemeinsames Bahnstück |
| `AIM t` | t Frames auf den Spieler zulenken (Seek) |
| `FIRE k` | Schuss der Art k (oder Salve) |
| `WAIT t` | stehen bleiben |
| `SPEED`, `ANIM` | Tempo/Animation ändern |
| `END` | Bahn verlassen (Gegner fliegt aus dem Bild) |

So lassen sich die heutigen Sinusschlangen und auch Sturzflüge, Kreise und Zielanflüge beschreiben. Eine
typische Bahn hat 10–30 Byte.

### 2.5 Werkzeug
Leveldesign erfolgt am PC:
- **Karte** in *Tiled* (frei, Tilesets aus PNG). Alternativ kann ChatGPT eine JSON-Karte im Format von PR #4 liefern.
- **Ereignisse** als Objekt-Ebene in Tiled oder als Textdatei, z. B. `@row 40: formation 3 x=120 mirror`.
- **Bahnen** als Text (`move 0,4,32` / `aim 20` / `fire red` …).
- Ein Python-Werkzeug `tools/build_level.py` erzeugt daraus die gepackten Dateien und prüft Budgets
  (Glyphen, Paletten, Speicher). Ein Bild des Levels mit eingezeichneten Ereignissen dient zur Kontrolle.

### 2.6 Entscheidungen (01.11.2026)
1. **Leveldesign als Text/JSON**, damit ChatGPT Level erzeugen kann: `docs/level_json.md`.
2. **Shops als Overlay** über dem Spielbildschirm.
3. **Levellänge etwa 4 Minuten** (≈ 375 Kartenzeilen).

Umgesetzt in Stage 3a: zwei Dateien pro Level (`LnGFX`, `LnDAT`), noch ungepackt. ZX0 folgt, wenn die
Dateien größer werden.

## Quellen
- [NESdev Wiki: Level compression](https://nesdev.org/wiki/Level_compression): objektbasierte Karten, Metatiles, Chunks, Spaltenvorlagen, RLE/LZ, Auto-Tiling
- [breadbin wiki: Working with Maps, Tiles, Chars and Compression](https://github.com/cbmeeks/breadbin-legacy/wiki/Working-with-Maps,-Tiles,-Chars-and-Compression): C64-Hierarchie Zeichen → Tiles → Meta-Tiles → Räume, Bytebeispiele
- [MushROMs: SMB1 Level Format](https://github.com/bonimy/MushROMs/blob/master/doc/SMB1%20Level%20Format.md): Byteformat der Objekt- und Gegnerlisten von *Super Mario Bros.*
- [Codetapper: Menace Part 4 – Aliens](https://codetapper.com/amiga/diary-of-a-game/menace/part-4-aliens): Gegnerdatensatz, Bahnbefehle
- [Codetapper: Menace Part 5 – Aliens 2](https://codetapper.com/amiga/diary-of-a-game/menace/part-5-aliens-2): Bahn-Datei pro Level, Befehle im ungültigen Koordinatenbereich
- [Codetapper: Uridium 2 Part 5](https://codetapper.com/amiga/diary-of-a-game/uridium-2/uridium-2-part-5): gespiegelte Bahnen per Flag, Laden ganzer Gegnergruppen
- [Codetapper: Mayhem in Monsterland Part 2](https://codetapper.com/c64/diary-of-a-game/mayhem-in-monsterland/lets-make-a-monster-part-2): Gegner an den Scroll-Level gekoppelt, Entpackroutinen
- [Computer Archeology: Galaga](https://computerarcheology.com/Arcade/Galaga): Befehlsverteiler und Unterbefehle der Gegnersteuerung
- [Data Crystal: Zanac ROM map](https://datacrystal.tcrf.net/wiki/Zanac/ROM_map): RLE-gepackte Grafiksätze pro Gebietsgruppe
- [AtariAge: Scrolling shoots and attacking waves](https://forums.atariage.com/topic/191366-scrolling-shoots-and-attacking-waves/): feste Wellen in *Armalyte*
