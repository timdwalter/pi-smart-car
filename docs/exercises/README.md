# SmartCar – Übungen

Kleine, aufeinander aufbauende Übungen rund um den Freenove 4WD SmartCar (Raspberry Pi 4 + Kamera). Sie sind für Workshops wie eine Hackerschool gedacht. Jede Übung hat ein lauffähiges Skript in `pi/` und eine Erklärung hier.

**Langfristiges Ziel:** Das Auto erkennt ein grünes Blatt Papier auf dem Boden, dreht sich dorthin, fährt hin und parkt darauf.

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
| 5 | *geplant:* Zum Blatt drehen | Erkennung + Drehen kombinieren | **ja** |
| 6 | *geplant:* Hinfahren und parken | Zustandsautomat, Kalibrierung | **ja** |

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
