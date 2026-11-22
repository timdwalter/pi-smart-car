# SmartCar – Übungen

Kleine, aufeinander aufbauende Übungen rund um den Freenove 4WD SmartCar (Raspberry Pi 4 + Kamera). Sie sind für Workshops wie eine Hackerschool gedacht. Jede Übung hat ein lauffähiges Skript in `pi/` und eine Erklärung hier.

**Langfristiges Ziel:** Das Auto erkennt ein grünes Blatt Papier auf dem Boden, dreht sich dorthin, fährt hin und parkt darauf.

Alle Übungen gibt es zusammen mit Einstieg, Projektaufgaben und Glossar auch als **Lehrbuch** in einer HTML-Datei: `python tools/build_lehrbuch.py` erzeugt `dist/SmartCar_Lehrbuch.html`.

## Aufbau jeder Übung

Jede Übungsdatei besteht aus zwei Teilen:

| Teil | Inhalt | Einsatz |
|---|---|---|
| **Lernziele** | Was man danach kann | Einstieg |
| **Teil A – Lecture** | Problem, Hintergrund, Theorie Schritt für Schritt, Code-Ausschnitte, Bilder und Ergebnisse aus echten Testläufen | zum **Vortragen** oder Selbstlesen |
| **Teil B – Exercise** | Sicherheit, Befehle zum Ausprobieren, Aufgaben, Lösungen zum Aufklappen | zum **selbst Machen** am Auto |

## Übersicht

| # | Übung | Thema | Bewegt sich das Auto? |
|---|---|---|---|
| 1 | [Kamerakopf bewegen](head_movement_exercise_1.md) | Servos, Kamera, systematisch messen | nur der Kamerakopf |
| 2 | [Grünes Blatt erkennen](cv_exercise_1.md) | Bildverarbeitung mit OpenCV, HSV-Farbraum, Masken, Konturen | nur der Kamerakopf |
| 3 | [Vorwärts und rückwärts fahren](drive_exercise_1.md) | Motoren, PWM, Sicherheits-Checks, Ultraschall | **ja** |
| 4 | [Um 90° drehen – ohne Gyroskop](turn_exercise_1.md) ⭐ | Visuelle Odometrie: ORB-Features, Matching, Lochkamera-Modell, Regelkreis | **ja** |
| 4b | *geplant:* Kontinuierlich drehen mit laufender Überwachung | Optischer Fluss, hohe Bildrate, Regler mit Bremsen | **ja** |
| 5 | [Blatt suchen und ausrichten](align_exercise_1.md) | Zustandsautomat, Visual Servoing, Kalibrierung des Kamerakopfs | **ja** |
| 5b | [Kamera und Fahrzeug kalibrieren](calibration_exercise_1.md) | Pan-Nullpunkt, Geschwindigkeit, toter Winkel, Bodenmodell, korrelierte Parameter | Kamerakopf (+ einmal kurz fahren) |
| 6 | [Hinfahren und parken](park_exercise_1.md) | Toter Winkel, Koppelnavigation, Bezugspunkt, Fehlersuche | **ja** |
| 7 | [Die ganze Mission](mission_exercise_1.md) ⭐ | Umschauen, suchen, ausrichten, hinfahren, parken in einem Programm | **ja** |

## Bekannte Hardware-Schwierigkeiten

Die Übungen zeigen bewusst auch, was an echter Hardware schiefgeht. Bei diesem Auto:

| Problem | Auswirkung | Behandelt in |
|---|---|---|
| **4WD ohne Lenkung, Reifen nicht ideal** | Beim Drehen rutschen die Räder, die Drehrate schwankt stark (42–62°/s) | [Übung 4](turn_exercise_1.md) |
| **Kein Gyroskop, keine Radencoder** | Drehwinkel und Strecke müssen anders gemessen werden (Kamera, Zeit) | [Übung 4](turn_exercise_1.md), [Übung 6](park_exercise_1.md) |
| **Kamerakopf verdreht** | Pan 90 schaut ~18° nach links, geradeaus = Pan 66 | [Übung 5](align_exercise_1.md) |
| **Kamerakopf instabil** | Kabel verschieben sich beim Drehen, verhaken sich und verkippen den Kopf. Die Kalibrierung kann sich ändern. | [Übung 5](align_exercise_1.md) |
| **Spiegelnder Laminatboden** | Lichtreflexe stören die Erkennung markanter Punkte | [Übung 4](turn_exercise_1.md) |
| **Akku** | Tiefentladen gibt es keine Kraft, die Spannung sinkt unter Last. Einzelne ADC-Messungen springen (z. B. 6,6 V statt 7,0 V). | [Übung 3](drive_exercise_1.md), [Übung 7](mission_exercise_1.md) |
| **Licht** | Bei Kunstlicht: lange Belichtung (Bewegungsunschärfe), Rauschen, blasse Farben | [Übung 2](cv_exercise_1.md), [Übung 5](align_exercise_1.md) |
| **Anfahrverzug** | Kurze Fahrimpulse fahren deutlich weniger als Geschwindigkeit × Zeit | [Übung 6](park_exercise_1.md) |

## Voraussetzungen

- Zugang zum Pi, siehe [KOLLEGEN_ANLEITUNG.md](../KOLLEGEN_ANLEITUNG.md)
- Hardware-Details und Befehle: [OPERATIONS_MANUAL.md](../OPERATIONS_MANUAL.md)

## Skripte auf den Pi bringen und starten

```
export MSYS_NO_PATHCONV=1          # nur in Git Bash unter Windows nötig
.venv/Scripts/python.exe tools/pi.py put pi/<skript>.py /home/pi/smartcar/<skript>.py
.venv/Scripts/python.exe tools/pi.py run "cd ~/smartcar && python3 <skript>.py <argumente>"
.venv/Scripts/python.exe tools/pi.py get /home/pi/smartcar/debug/<bild>.jpg debug/<bild>.jpg
```

Bilder aus den echten Testläufen liegen in [`images/`](images/) und sind in die Übungen eingebunden.

Der Pi hat keinen Bildschirm. Alle Skripte speichern deshalb **Bilder** nach `~/smartcar/debug/`, die anschließend auf den eigenen Rechner geholt und dort angesehen werden.
