# SmartCar – Operations Manual

Bedienung, Hardware-Belegung und Befehle für den Betrieb des SmartCars. Alle Werte wurden am echten Gerät gemessen bzw. getestet.

Stand: 2026-11-22

---

## 1. Steckbrief

| Komponente | Details |
|---|---|
| Auto | Freenove 4WD Smart Car Kit for Raspberry Pi (normale Räder, kein Mecanum) |
| Rechner | Raspberry Pi 4 Model B Rev 1.1, Debian 12 (Bookworm), Python 3.11.2 |
| Kamera | OV5647 (Pi Camera v1), max. 2592×1944, über `picamera2` |
| Bibliotheken (systemweit) | OpenCV 4.6.0, picamera2 |
| Akkus | 2× 18650 Li-Ion, 2S (voll 8,4 V) |
| Hostname / User | `raspberrypi` / `pi` (sudo ohne Passwort) |
| Tailscale | Gerät `smartcar`, IP `100.77.136.52` |
| Freenove-Code | `/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server` |
| Eigener Code auf dem Pi | `/home/pi/smartcar/` |
| Debug-Ausgaben | Pi: `/home/pi/smartcar/debug/`, PC: `debug/` (nicht im Repo) |

---

## 2. Inbetriebnahme

1. **Akkus einsetzen** (2× 18650, auf die Polung achten).
2. **Schalter einschalten.** Es gibt eine Versorgung für den Pi und einen **separaten Schalter für den Motorstrom**. Ist der Motorschalter aus, misst der ADC 0 V und die Räder drehen sich nicht, obwohl der Pi läuft.
3. **Warten**, bis der Pi hochgefahren ist (ca. 30–60 s).
4. **Verbindung prüfen:**
   ```
   .venv/Scripts/python.exe tools/pi.py run "hostname; uptime -p"
   ```
5. **Akkuspannung prüfen** (siehe Abschnitt 4). Vor jedem Fahrtest!

### Herunterfahren
```
.venv/Scripts/python.exe tools/pi.py run "sudo shutdown -h now"
```
Warten, bis die grüne LED am Pi nicht mehr blinkt, dann die Schalter ausschalten. **Den Motorschalter nicht eingeschaltet lassen**, wenn das Auto nicht benutzt wird, sonst entladen sich die Akkus.

---

## 3. Verbindung vom PC

Zugangsdaten stehen in `.env` (Vorlage `.env.example`). Der SSH-Helfer `tools/pi.py` liest sie selbst ein.

| Befehl | Zweck |
|---|---|
| `.venv/Scripts/python.exe tools/pi.py run "<befehl>"` | Befehl auf dem Pi ausführen |
| `.venv/Scripts/python.exe tools/pi.py put <lokal> <remote>` | Datei auf den Pi kopieren |
| `.venv/Scripts/python.exe tools/pi.py get <remote> <lokal>` | Datei vom Pi holen |

> ⚠️ **Git Bash unter Windows:** Bei `put`/`get` mit Pfaden wie `/home/pi/...` vorher `export MSYS_NO_PATHCONV=1` setzen. Sonst schreibt Git Bash den Pfad in einen Windows-Pfad um, und es kommt der Fehler „No such file“. In PowerShell oder cmd tritt das nicht auf.

Von außerhalb des Heimnetzes: Tailscale muss auf dem PC laufen, und in `.env` steht `PI_HOST=smartcar` oder `PI_HOST=100.77.136.52`. Siehe [ADMIN_REMOTE.md](ADMIN_REMOTE.md).

---

## 4. Akku

```python
from ADC import Adc
spannung = Adc().recvADC(2) * 3
```

| Spannung | Zustand |
|---|---|
| 8,4 V | voll |
| ≥ 7,0 V | gut |
| 6,5–7,0 V | wird knapp, bald laden |
| < 6,5 V | zu schwach für zuverlässiges Fahren, **laden** |
| ~0 V | **Motorschalter aus** oder keine Akkus eingesetzt |

Unter Last (Motoren an) sinkt die Spannung kurz um ca. 0,3–0,5 V, das ist normal.

`ADC.py` enthält zusätzlich `calcPowerLevel(spannung)`. Die Funktion rechnet 5,6–8,4 V in 0–1 um (lokale Änderung, nicht von Freenove).

**Erfahrung:** Bei ca. 4 V (tiefentladen) haben sich die Räder kaum bewegt. Tiefentladene Li-Ion-Zellen beim Laden beobachten. Werden sie heiß oder halten sie keine Spannung, müssen sie ersetzt werden.

---

## 5. Motoren

```python
from Motor import Motor
m = Motor()
m.setMotorModel(vorne_links, hinten_links, vorne_rechts, hinten_rechts)
```

- Wertebereich ca. **−4095 … 4095**, das Vorzeichen bestimmt die Richtung, 0 = Stopp.
- Läuft **ohne `sudo`**.

| Bewegung | Befehl |
|---|---|
| Vorwärts | `(2000, 2000, 2000, 2000)` |
| Rückwärts | `(-2000, -2000, -2000, -2000)` |
| Auf der Stelle links drehen | `(-x, -x, x, x)` |
| Auf der Stelle rechts drehen | `(x, x, -x, -x)` |
| Kurve links (Freenove-Test) | `(-2000, -2000, 4000, 4000)` |
| Stopp | `(0, 0, 0, 0)` |

### ⚠️ Sicherheitsregeln
1. **Vor jedem Motortest klären:** Ist das Auto **aufgebockt** oder steht es **auf dem Boden**? Remote ist das nicht zu erkennen.
2. **Motorbefehle immer zeitlich begrenzen** und im `finally` stoppen:
   ```python
   try:
       m.setMotorModel(2000, 2000, 2000, 2000)
       time.sleep(1)
   finally:
       m.setMotorModel(0, 0, 0, 0)
   ```
3. Die Motortreiber-Bausteine (PCA9685) **behalten den letzten Befehl**, auch wenn das Python-Skript abstürzt oder per `timeout` beendet wird. Im Notfall:
   ```
   .venv/Scripts/python.exe tools/pi.py run "cd ~/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server && python3 -c 'from Motor import Motor; Motor().setMotorModel(0,0,0,0)'"
   ```

---

## 6. Kamera-Servos (Pan/Tilt)

```python
from servo import Servo
s = Servo()
s.setServoPwm('0', winkel)   # Tilt
s.setServoPwm('1', winkel)   # Pan
```

**Belegung per Scan ermittelt.** Die Kommentare in Freenoves `test.py` legen eine andere Belegung nahe, maßgeblich ist der Scan.

### Kanal `'0'` = Tilt (hoch/runter)
Kleinerer Wert = Kamera nach **oben**, größerer Wert = nach **unten**.

| Winkel | Blick |
|---|---|
| 50–70 | schräg nach oben (Wand, Decke) |
| 80 | ungefähr geradeaus, Horizont nahe der Bildmitte |
| **90** | **Suchen:** Horizont im oberen Viertel, Boden bis in die Ferne sichtbar |
| 100 | überwiegend Boden, Ferne nur als schmaler Streifen ganz oben (zu steil zum Suchen) |
| **110** | **Nahbereich:** nur Boden direkt vor dem Auto (für die letzte Annäherung) |

Getestet: 50–110. Über 110 ist noch nicht getestet, wegen eines möglichen mechanischen Anschlags vorsichtig herantasten.

### Kanal `'1'` = Pan (links/rechts)
| Winkel | Blick |
|---|---|
| 60 | links |
| 90 | ungefähr Mitte |
| 150 | rechts. Ab ca. 130 ist der eigene Reifen unten im Bild |

Getestet: 60–150.

### Servo-Scan
Mit `pi/head_movement_exercise_1.py` lässt sich die Kamera durch mehrere Winkel fahren, mit je einem Bild pro Winkel:
```
export MSYS_NO_PATHCONV=1
.venv/Scripts/python.exe tools/pi.py put pi/head_movement_exercise_1.py /home/pi/smartcar/head_movement_exercise_1.py
.venv/Scripts/python.exe tools/pi.py run "cd ~/smartcar && python3 head_movement_exercise_1.py 0 90 100 110"
.venv/Scripts/python.exe tools/pi.py get /home/pi/smartcar/debug/scan_0_100.jpg debug/scan_0_100.jpg
```
Am Ende fährt der gescannte Kanal zurück auf 90.

---

## 7. Kamera

```python
from picamera2 import Picamera2
cam = Picamera2()
cam.configure(cam.create_still_configuration(main={"size": (640, 480)}))
cam.start(); time.sleep(2)          # Belichtung einschwingen lassen
cam.capture_file("/home/pi/smartcar/debug/bild.jpg")
cam.stop()
```

- Kamera prüfen: `rpicam-hello --list-cameras`
- Verfügbare Sensor-Modi: 640×480 (59 fps), 1296×972 (43 fps), 1920×1080 (31 fps), 2592×1944 (16 fps)
- **Nicht `cv2.VideoCapture` verwenden.** Auf Bookworm funktioniert die Pi-Kamera darüber oft nicht.
- **Kein `cv2.imshow`.** Über SSH gibt es keinen Bildschirm. Stattdessen Bilder speichern und per `get` auf den PC holen.
- Es kann immer nur ein Prozess die Kamera nutzen. Läuft z. B. der Freenove-Server, ist die Kamera belegt.

---

## 8. Weitere Sensoren und Freenove-Testskript

| Sensor | Aufruf |
|---|---|
| Ultraschall | `from Ultrasonic import Ultrasonic; Ultrasonic().get_distance()` → cm |
| Line-Tracking (IR) | siehe `Line_Tracking.py` |
| LEDs | `Led.py`, **braucht `sudo`** |
| Buzzer | `Buzzer.py` |

Freenove-Testskript (im Server-Ordner):
```
sudo python3 test.py Motor|Servo|Ultrasonic|Led|ADC|Buzzer|Infrared|Rotate
```
**`sudo` ist Pflicht**, weil `test.py` beim Start die LED-Bibliothek (`rpi_ws281x`) lädt und diese `/dev/mem` braucht. Ohne `sudo` gibt es `Can't open /dev/mem` und einen Segfault.

---

## 9. Testumgebung (aktuell)

- Fahrfläche: **helles Laminat**, neutral, nichts Grünes in der Umgebung. Im Raum stehen blaue Faszienrolle, Hantelbank, Hanteln und weiße Schränke.
- Ziel: grünes Blatt Papier auf dem Boden.

---

## 10. Fehlerbehebung

| Problem | Ursache / Lösung |
|---|---|
| Räder drehen sich nicht, Befehle laufen ohne Fehler | Motorschalter aus (Akku zeigt ~0 V) oder Akku leer (< 6,5 V) |
| `Can't open /dev/mem` / Segfault | Skript importiert die LED-Lib, mit `sudo` starten |
| `get`/`put`: „No such file“, obwohl die Datei existiert | Git-Bash-Pfadumwandlung, `export MSYS_NO_PATHCONV=1` |
| `UnicodeEncodeError` in `pi.py` | in aktueller Version behoben (UTF-8-Ausgabe) |
| Pi nicht erreichbar | Hochgefahren? Tailscale am PC aktiv? `PI_HOST` in `.env` korrekt? |
| Kamera „busy“ | Ein anderer Prozess nutzt die Kamera (z. B. Freenove-Server), beenden |
| Motoren laufen nach Absturz weiter | Not-Stopp-Befehl aus Abschnitt 5 |

---

## 11. Übungen / Skripte

Alle Skripte liegen im Repo unter `pi/` und werden nach `/home/pi/smartcar/` kopiert:
```
export MSYS_NO_PATHCONV=1
.venv/Scripts/python.exe tools/pi.py put pi/<skript>.py /home/pi/smartcar/<skript>.py
.venv/Scripts/python.exe tools/pi.py run "cd ~/smartcar && python3 <skript>.py <argumente>"
```

| Skript | Zweck | Aufruf |
|---|---|---|
| `head_movement_exercise_1.py` | Kamerakopf durch Winkel fahren, je ein Bild | `python3 head_movement_exercise_1.py <kanal> <winkel...>` |
| `cv_exercise_1.py` | Grünes Blatt im Bild erkennen | `python3 cv_exercise_1.py [tilt=90] [pan=90]` |
| `drive_exercise_1.py` | Vor- und zurückfahren mit Akku- und Ultraschall-Check | `python3 drive_exercise_1.py [speed=1500] [sekunden=2]` (speed 0 = Trockenlauf) |
| `turn_exercise_1.py` | Auf der Stelle um einen Winkel drehen, gemessen per Kamera | `python3 turn_exercise_1.py [winkel=90] [links\|rechts] [speed=2000]` (speed 0 = Trockenlauf) |

Ausführliche Erklärungen mit Aufgaben: [docs/exercises/](exercises/README.md)

### Grün-Erkennung (`cv_exercise_1.py`)
- Ablauf: Bild (640×480) → HSV → `inRange` → Morphologie (Öffnen/Schließen) → größte Kontur → Schwerpunkt
- **HSV-Bereich:** H 35–95, S ≥ 60, V ≥ 40 (OpenCV-Skala H 0–179)
- **Gemessene Farben (2026-11-22):**
  | Objekt | HSV |
  |---|---|
  | Grünes Testblatt | H 80–87, S 170–205, V 160–175 (eher **blaugrün**) |
  | Laminatboden | H ~8, S ~36, V ~222 |
  | Blaue Faszienrolle | Blau, H > 100, wird nicht erkannt |
- Mit der ersten Obergrenze H ≤ 85 zerfiel das Blatt in Stücke, weil es blaugrün ist. Deshalb liegt die Grenze jetzt bei 95.
- **Ausgabewerte:**
  - `offset_x`: −1 = ganz links, 0 = Bildmitte, +1 = ganz rechts. Daraus ergibt sich die Drehrichtung.
  - `pos_y`: 0 = oberer Bildrand (weit weg), 1 = unterer Bildrand (nah). Das ist ein Maß für die Entfernung.
  - `area_fraction`: Anteil des Bildes, der grün ist
- Debug-Bilder: `cv1_raw.jpg`, `cv1_mask.jpg`, `cv1_overlay.jpg` in `~/smartcar/debug/`
- Erster Test: Das Blatt lag weit weg und schräg rechts.
  | Tilt | pos_y | Fläche |
  |---|---|---|
  | 80 | 0,48 | 0,7 % |
  | 85 | 0,38 | 0,7 % |
  | 90 | 0,29 | 0,8 % |
  | 100 | 0,11 | 1,0 % |
  Bei Tilt 100 klebt das Blatt am oberen Bildrand, deshalb wird mit **Tilt 90 gesucht**.
- Die Kamera sitzt nur ca. 10 cm über dem Boden. Ein entferntes Blatt erscheint deshalb immer als flacher Streifen.

### Fahren (`drive_exercise_1.py`)
- 1500 für 1 s vor und zurück funktioniert. Beim Anfahren bricht der Akku kurz von ~7,9 V auf ~7,3 V ein.
- Ultraschall vorne zeigt im freien Raum ~150 cm.
- Geschwindigkeit in cm/s ist **noch nicht kalibriert**.

### Drehen ohne Gyroskop (`turn_exercise_1.py`)
- **Sensorlage:** Am I2C-Bus (`sudo i2cdetect -y 1`) hängen nur `0x40` (PCA9685, Motoren/Servos) und `0x48` (ADS7830, ADC). Es gibt **kein Gyroskop/IMU** (MPU-6050 wäre `0x68`) und keine Radencoder.
- **Verfahren:** visuelle Odometrie. Foto, Drehimpuls, Foto, ORB-Features matchen, horizontale Verschiebung über das Lochkamera-Modell in Grad umrechnen (f = 320 / tan(53,5°/2) ≈ 634 px), Median mit Ausreißer-Filter, aufsummieren.
- **Drehrate** bei Speed 2000 auf Laminat: **42–62°/s**, schwankt stark je nach Ausrichtung. Die Reifen des Kits greifen beim Skid-Steering ungleichmäßig.
- Impulse höchstens **0,3 s** (~18°), sonst überlappen die Bilder zu wenig. Kamera dabei auf Tilt 80 / Pan 90.
- Weiße Wände oder Heizung liefern kaum Features. Dann wird der Winkel aus der Drehrate geschätzt (max. 2× hintereinander).
- Features nur in den **oberen 55 % des Bildes** (`ROI_TOP_FRACTION`), weil der Boden nah ist und spiegelt. Die Ausreißer-Toleranz wächst mit dem Winkel (Parallaxe, Kamera sitzt vor der Drehachse).
- Testläufe: 87,2° / 91,4° / 87,8° / 89,3° gemessen, real jeweils **knapp unter 90°** (nach Augenmaß), Genauigkeit grob ±5°.
- Bewusst **schrittweise** (Stop-and-Go). Kontinuierliches Drehen mit laufender Überwachung ist eine eigene, geplante Übung.
- Erster Testlauf: Ziel 90°, gemessen **87,2°**. Real noch nicht nachgemessen. `HFOV_DEG = 53,5` stammt aus dem Datenblatt und ist **noch nicht kalibriert**.
- **Nachrüst-Option:** MPU-6050 (I2C) für eine Gyro-Messung.
