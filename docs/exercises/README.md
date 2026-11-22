# SmartCar – Übungen

Kleine, aufeinander aufbauende Übungen rund um den Freenove 4WD SmartCar (Raspberry Pi 4 + Kamera). Sie sind für Workshops wie eine Hackerschool gedacht. Jede Übung hat ein lauffähiges Skript in `pi/` und eine Erklärung hier.

**Langfristiges Ziel:** Das Auto erkennt ein grünes Blatt Papier auf dem Boden, dreht sich dorthin, fährt hin und parkt darauf.

| # | Übung | Thema | Bewegt sich das Auto? |
|---|---|---|---|
| 1 | [Kamerakopf bewegen](head_movement_exercise_1.md) | Servos, Kamera, systematisch messen | nur der Kamerakopf |
| 2 | [Grünes Blatt erkennen](cv_exercise_1.md) | Bildverarbeitung mit OpenCV, HSV-Farbraum, Masken, Konturen | nur der Kamerakopf |
| 3 | *geplant:* Zum Blatt drehen | Regelkreis: Kamera → Entscheidung → Motor | **ja** |
| 4 | *geplant:* Hinfahren und parken | Zustandsautomat, Kalibrierung | **ja** |

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

Der Pi hat keinen Bildschirm. Alle Skripte speichern deshalb **Bilder** nach `~/smartcar/debug/`, die anschließend auf den eigenen Rechner geholt und dort angesehen werden.
