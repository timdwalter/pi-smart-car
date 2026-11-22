# Übung 6: Hinfahren und auf dem Blatt parken

**Skript:** [`pi/park_exercise_1.py`](../../pi/park_exercise_1.py)
**Dauer:** ca. 60–90 Minuten (inkl. Kalibrierung)
**Bewegt sich:** **ja**, das Auto fährt vorwärts und korrigiert die Richtung
**Voraussetzung:** [Übung 3](drive_exercise_1.md) (Fahren), [Übung 5](align_exercise_1.md) (Ausrichten)

> **Status:** Das Skript ist **vorbereitet, aber noch nicht am Auto getestet**. Es fehlen die Kalibrierwerte (siehe Teil B).

> **Teil A – Lecture:** Theorie und Erklärungen, zum Vortragen oder Selbstlesen.  
> **Teil B – Exercise:** Praxis am Auto, Aufgaben und Lösungen zum Aufklappen.

## Lernziele

- Ein **Zustandsautomat** mit mehreren Phasen
- Warum eine Kamera einen **toten Winkel** hat und wie man ihn überbrückt
- **Kalibrieren:** Messwerte aus der echten Welt in Programmkonstanten übersetzen
- **Koppelnavigation** (Dead Reckoning): die letzten Zentimeter ohne Sicht fahren

---

## Teil A – Lecture

### Das Problem

Das Auto ist auf das Blatt ausgerichtet (Übung 5). Jetzt soll es hinfahren und **mittig auf dem Blatt** anhalten.

Die Schwierigkeit: **Kurz bevor das Auto auf dem Blatt steht, sieht die Kamera das Blatt nicht mehr.** Die Kamera schaut schräg nach vorne. Direkt vor und unter dem Auto liegt ein Bereich, den sie nicht erfassen kann, der **tote Winkel**.

```
   Kamera
     ◉ ╲
     │   ╲   Sichtbereich bei Tilt 110
     │     ╲
  ═══╪═══════╲════════════════   Boden
     │◀─────▶│
     toter Winkel (nicht sichtbar)
```

### Die Phasen (Zustandsautomat)

| Zustand | Was passiert | Übergang |
|---|---|---|
| **ANFAHREN (fern)** | Kamera auf Tilt 90. Kurze Vorwärtsimpulse (0,4 s). Nach jedem Impuls Blatt suchen, bei > 5° Abweichung Richtung korrigieren. | Blatt erreicht `pos_y > 0,75` → Kamera senken |
| **ANFAHREN (nah)** | Kamera auf Tilt 110, sonst wie oben | Vordere Blattkante berührt den unteren Bildrand → EINPARKEN |
| **EINPARKEN** | Restliche Strecke **blind** fahren (Koppelnavigation) | → FERTIG |

Sicherheitsnetz: Der Ultraschall stoppt bei einem Hindernis < 15 cm. Verliert das Programm das Blatt aus dem Blick, bricht es ab.

### Die blinde Reststrecke

Sobald die vordere Blattkante unten aus dem Bild verschwindet, ist sie genau **`TOTER_WINKEL_CM`** von der Kamera entfernt. Bis die **Mitte des Autos** über der **Mitte des Blattes** steht, fehlen noch:

```
rest_cm = TOTER_WINKEL_CM + BLATT_LAENGE_CM / 2 − KAMERA_VOR_MITTE_CM
rest_s  = rest_cm / SPEED_CM_PER_S
```

```
                   Kamera   Mitte Auto
                     ◉──────────●
  Boden  ───────────[══════ grünes Blatt ══════]──────
                     │◀ toter ▶│◀ Blatt/2 ▶│
                       Winkel
         Auto fährt: toter Winkel + Blatt/2 − (Kamera vor Mitte)
```

Für diese Rechnung braucht man drei **Kalibrierwerte**, die man nur am echten Auto messen kann:

| Wert | Bedeutung | Wie messen |
|---|---|---|
| `SPEED_CM_PER_S` | Fahrgeschwindigkeit bei Speed 1500 | Übung 3, Aufgabe 2: 1 s fahren, Strecke messen |
| `TOTER_WINKEL_CM` | Bodenabstand Kamera → unterer Bildrand bei Tilt 110 | Maßband vor das Auto legen, Kalibrierbild ansehen |
| `KAMERA_VOR_MITTE_CM` | Wie weit die Kamera vor der Automitte sitzt | Lineal |

### Warum die Geschwindigkeit das schwächste Glied ist

Die blinde Strecke ist **Koppelnavigation**: Zeit × Geschwindigkeit. Wie in Übung 4 gilt auch hier, dass die Mechanik nicht exakt tut, was man befiehlt:
- **Anfahren:** Das Auto braucht einen Moment, bis es auf Geschwindigkeit ist, und rollt nach dem Abschalten noch etwas nach.
- **Akkustand:** Mit sinkender Spannung fährt das Auto langsamer.
- **Untergrund:** Auf dem Papier haben die Reifen anders Grip als auf dem Laminat.

Je **kürzer** die blinde Strecke, desto kleiner der Fehler. Deshalb wird die Kamera im Nahbereich auf Tilt 110 gesenkt: Der tote Winkel wird kleiner.

### Ergebnisse

*Noch keine. Das Skript ist vorbereitet, aber noch nicht kalibriert und getestet.*

---

## Teil B – Exercise

### Sicherheit

- Das Auto **fährt vorwärts**. Vorher klären, ob der Weg zum Blatt frei ist.
- Ultraschall-Not-Stopp bei < 15 cm, maximal 60 Schritte.
- Ohne Kalibrierwerte verweigert das Skript den Start.

### Kalibrieren

```
python3 park_exercise_1.py kalibrieren
```
Das Skript stellt die Kamera auf Tilt 110 und speichert `~/smartcar/debug/park_kalibrierung_tilt110.jpg`. Ein Maßband längs vor das Auto legen und ablesen, welcher Abstand gerade noch am unteren Bildrand sichtbar ist. Die drei Werte oben im Skript eintragen.

### Ausprobieren

```
python3 align_exercise_1.py rechts 2000    # erst ausrichten (Übung 5)
python3 park_exercise_1.py 1500            # dann hinfahren und parken
```

Debug-Bilder: `~/smartcar/debug/park_<schritt>.jpg`

### Aufgaben

1. **Kalibrieren:** Die drei Werte messen und eintragen. Wie groß ist der tote Winkel bei Tilt 110? Und bei Tilt 90?
2. **Erster Parkversuch:** Wie weit liegt die Automitte nach dem Parken neben der Blattmitte, längs und quer?
3. **Fehlerquelle finden:** Parkt das Auto zu früh oder zu spät? Welcher Kalibrierwert ist vermutlich falsch?
4. **Hochkant oder quer:** Das Blatt einmal längs (29,7 cm) und einmal quer (21 cm) zur Fahrtrichtung legen. Was muss im Skript angepasst werden?
5. **Weit weg:** Das Blatt 2 m entfernt hinlegen. Funktioniert die Erkennung aus der Ferne? Ab welcher Entfernung nicht mehr?
6. **Bonus:** Übung 5 und 6 zu **einem** Programm zusammenführen: suchen → ausrichten → anfahren → parken.
7. **Bonus:** Die Blattlänge **messen statt eintragen**: Aus der Höhe der Bounding-Box im Bild und dem Kamerawinkel lässt sich die Entfernung schätzen. Wie?

### Lösungen

*Folgen nach dem ersten Testlauf.*
