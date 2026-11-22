# Weiter geht's: Projektaufgaben

Stufe 1 ist erreicht, fertig ist das Projekt aber nicht. Die folgenden Aufgaben sind offene Baustellen, die sich gut für IoT-Hacking-Abende eignen. Sie sind nach Schwierigkeit sortiert:

- 🟢 **Einstieg:** in einem Abend machbar, wenig Vorwissen nötig
- 🟡 **Fortgeschritten:** setzt die entsprechenden Übungen voraus
- 🔴 **Projekt:** mehrere Abende, eigene Recherche, eventuell neue Hardware

## So läuft ein Beitrag ab

1. Kurz in der Runde Bescheid geben, welche Aufgabe gerade bearbeitet wird, und wer wann am Auto arbeitet (nur eine Person gleichzeitig an den Motoren).
2. Eigener Code kommt nach `pi/`, gemeinsame Kalibrierwerte nach `pi/car_config.py`.
3. Neue Erkenntnisse (gemessene Werte, Fehler und Lösungen) ins Betriebshandbuch, den Fortschritt ins Statuslog von `PROJECT.md`.
4. Wird aus einer Aufgabe eine neue Übung, bekommt sie eine Erklärung in `docs/exercises/` im üblichen Aufbau (Lernziele, Teil A – Lecture, Teil B – Exercise) und einen Eintrag in `tools/build_lehrbuch.py`. Dann landet sie automatisch in der nächsten Ausgabe dieses Buches.

## Aufgaben

### 🟢 Kabelführung am Kamerakopf

Das Flachbandkabel der Kamera und die Servokabel ziehen beim Schwenken am Kopf und verdrehen ihn. Kabel mit Spiel verlegen, Zugentlastung am Chassis anbringen, Schrauben der Servo-Arme prüfen. Danach `calibrate_pan.py` erneut ausführen und `PAN_CENTER` aktualisieren.

*Vor Ort am Auto. Voraussetzung: Übung 1, Abschnitt Pan-Kalibrierung in Übung 5b.*

### 🟢 Parkgenauigkeit mit vollem Akku prüfen

Anfahrverzug und Geschwindigkeit wurden bei etwa 7,0 V gemessen. Mit frisch geladenem Akku (8,4 V) fährt das Auto schneller. Mehrere Parkläufe aus 100 und 150 cm messen und dokumentieren, wie stark die Abweichung vom Akkustand abhängt.

*Voraussetzung: Übung 6.*

### 🟡 Akkuspannung in die Fahrzeit einrechnen

Aufbauend auf der vorigen Aufgabe: die Geschwindigkeit als Funktion der Akkuspannung messen und die Blindstrecke beim Parken damit korrigieren. Für die Spannung den Median aus mehreren ADC-Messungen verwenden, Einzelwerte springen.

*Voraussetzung: Übung 3, 5b, 6.*

### 🟡 Bodenmodell bis 30 cm erweitern

Das Bodenmodell (Bildzeile → Abstand) ist mit Punkten bei 5, 10 und 20 cm kalibriert. Beim Parken liegt die Hinterkante des Blattes aber bei 21 bis 30 cm. Weitere Messpunkte aufnehmen, neu fitten und prüfen, ob sich die Parkgenauigkeit verbessert.

*Voraussetzung: Übung 5b.*

### 🟡 Bildwinkel der Kamera kalibrieren

Der horizontale Bildwinkel (`HFOV_DEG = 53,5`) stammt aus dem Datenblatt. Die daraus berechnete Brennweite von 634 px wurde in Übung 4 und 5b indirekt bestätigt, aber nie direkt gemessen. Eine eigene Messung (z. B. Objekt bekannter Breite in bekanntem Abstand) würde alle Winkelangaben absichern.

*Voraussetzung: Übung 2, 4.*

### 🔴 Übung 4b: kontinuierlich drehen

Bisher dreht das Auto im Stop-and-Go: Impuls, anhalten, Foto, messen. Das ist robust, aber langsam. Ziel ist eine Drehung mit laufender Überwachung: hohe Bildrate (640 × 480 bei 59 fps), optischer Fluss statt ORB-Matching, ein Regler, der rechtzeitig bremst. Das Ergebnis wird die geplante Übung 4b.

*Voraussetzung: Übung 4.*

### 🔴 Gyroskop nachrüsten

Ein MPU-6050 am I2C-Bus (Adresse `0x68`, aktuell frei) würde den Drehwinkel direkt messen. Spannend ist der Vergleich: Wie gut ist die visuelle Odometrie im Vergleich zum Gyro, und lassen sich beide kombinieren (Sensorfusion)?

*Neue Hardware nötig. Voraussetzung: Übung 4.*

### 🔴 Stufe 2: mehr als ein grünes Blatt

Mögliche Erweiterungen der Mission: mehrere Ziele nacheinander, Ziele in anderen Farben, Hindernisse auf dem Weg (Ultraschall), Ziele, die außer Sicht liegen. Vorher klären: Untergrund, Blattgröße, Aufbau der Testumgebung.

*Voraussetzung: Übung 7.*

## Infrastruktur

Neben den Fahr-Aufgaben gibt es zwei Themen rund um den Fernzugriff:

- **SSH-Key-Login** statt Passwort für alle, die regelmäßig mitarbeiten.
- **Draufsicht-Kamera** über dem Fahrbereich, damit remote zu sehen ist, wo das Auto steht und was es tut. Kamera und Standort sind noch offen.

Beides betrifft Netz und Zugänge und wird deshalb mit Tim abgesprochen, nicht im Alleingang umgesetzt.
