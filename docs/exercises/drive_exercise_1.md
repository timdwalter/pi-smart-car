# Übung 3: Vorwärts und rückwärts fahren

**Skript:** [`pi/drive_exercise_1.py`](../../pi/drive_exercise_1.py)
**Dauer:** ca. 20–30 Minuten
**Bewegt sich:** **ja**, das Auto fährt vor und zurück

> **Teil A – Lecture:** Theorie und Erklärungen, zum Vortragen oder Selbstlesen.  
> **Teil B – Exercise:** Praxis am Auto, Aufgaben und Lösungen zum Aufklappen.

## Lernziele

- Wie die vier Motoren angesteuert werden (**PWM-Werte**, Vorzeichen = Richtung)
- **Sicherheit zuerst:** Vorab-Checks und garantiertes Stoppen
- Warum der **Akku** unter Last einbricht
- Wie man mit dem **Ultraschallsensor** Hindernisse erkennt

---

## Teil A – Lecture

### Hintergrund

```python
motor.setMotorModel(vorne_links, hinten_links, vorne_rechts, hinten_rechts)
```
- Werte von −4095 bis +4095. Das ist die **Pulsweite (PWM)**, also wie viel Prozent der Zeit Strom fließt.
- Positiv = vorwärts, negativ = rückwärts, 0 = Stopp.
- Alle vier gleich → geradeaus. Links und rechts entgegengesetzt → auf der Stelle drehen (siehe [Übung 4](turn_exercise_1.md)).

**Wichtig:** Der Motortreiber **merkt sich den letzten Befehl**. Stürzt ein Programm ab, nachdem es „vorwärts“ gesagt hat, fährt das Auto weiter! Deshalb steht der Stopp-Befehl immer in einem `finally`-Block.

### Was das Skript macht

Aufruf: `python3 drive_exercise_1.py [geschwindigkeit=1500] [sekunden=2]`

1. **Vorab-Checks:**
   - Akkuspannung messen. Unter 6,5 V wird abgebrochen.
   - Ultraschall nach vorne messen. Ist ein Hindernis näher als 30 cm, wird abgebrochen.
2. **Vorwärts** fahren, alle 0,5 s die Akkuspannung ausgeben.
3. **0,5 s Pause.** Ein direkter Richtungswechsel würde Motoren und Akku stark belasten.
4. **Rückwärts** genauso lange.
5. **Stopp.** Das passiert immer, auch bei Fehlern, Ctrl+C oder wenn das Programm von außen beendet wird (`SIGTERM`).

Außerdem wird die Geschwindigkeit auf höchstens 3000 begrenzt.

### Ergebnisse aus dem Testlauf

#### Echter Lauf (2026-11-22, Laminatboden)
```
Akku: 7.89 V
Abstand vorne: 150 cm
Vorwärts: 1.0 s mit +1500
  Akku unter Last: 7.26 V      ← Spannungseinbruch beim Anfahren
  Akku unter Last: 7.92 V
Rückwärts: 1.0 s mit -1500
  Akku unter Last: 7.95 V
Fertig.
Motoren gestoppt.
```

---

## Teil B – Exercise

### Sicherheit

- Vorher klären: Ist das Auto **aufgebockt** oder steht es **auf dem Boden**? Ist **vorne und hinten** genug Platz? Nach hinten gibt es keinen Sensor!
- Mit kleinen Werten und kurzen Zeiten anfangen.

### Ausprobieren

```
python3 drive_exercise_1.py 0 0.5      # Trockenlauf: alle Checks, aber Motoren bleiben aus
python3 drive_exercise_1.py 1500 1     # 1 s vor, 1 s zurück
```

### Aufgaben

1. **Trockenlauf:** Mit Geschwindigkeit 0 starten. Funktionieren die Checks?
2. **Geschwindigkeit messen:** 1 s mit 1500 fahren und die Strecke mit dem Maßband messen. Wie viele cm/s sind das? Wiederholen mit 1000, 2000 und 2500. Ist der Zusammenhang linear?
3. **Mindestwert:** Ab welchem Wert bewegt sich das Auto überhaupt? Warum nicht schon bei 100? *Tipp: Haftreibung.*
4. **Zurück zum Start?** Steht das Auto nach vor und zurück wieder exakt am Start? Wenn nicht, warum?
5. **Spannungseinbruch:** Warum sinkt die Akkuspannung beim Anfahren am stärksten?
6. **Hindernis:** Eine Hand 20 cm vor den Ultraschallsensor halten und das Skript starten. Was passiert?
7. **Bonus:** Das Skript so umbauen, dass es eine Strecke in **cm** statt Sekunden fährt. Dafür braucht es das Ergebnis aus Aufgabe 2.
8. **Bonus:** Während der Fahrt **dauernd** den Ultraschall prüfen und anhalten, sobald etwas näher als 20 cm kommt.
