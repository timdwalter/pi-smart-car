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

**Einzelmessungen springen:** Einmal wurden 6,60 V gemessen, direkt danach 6,99–7,14 V. Für Entscheidungen (z. B. Abbruch bei zu wenig Spannung) den **Median aus mehreren Messungen** nehmen, wie in `mission_exercise_1.py`.

**Für das Parken** ist die Blindfahrt bei ~7,0–7,3 V kalibriert. Darunter fährt das Auto langsamer, die Reststrecke wird zu kurz.

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

⚠️ **Korrigiert am 2026-11-22:** **Größere Werte schauen nach LINKS**, ca. **0,85° pro Einheit** (kalibriert im Bereich 65–85).

⚠️ **Der Kamerakopf ist mechanisch verdreht: Bei Pan 90 schaut er ca. 18° nach links.** Pan 90 ist also **nicht** geradeaus. **Geradeaus = Pan 66** (`PAN_CENTER` in `pi/car_config.py`, kalibriert mit `pi/calibrate_pan.py`). Alle Skripte, die das Auto auf etwas ausrichten, müssen `PAN_CENTER` verwenden.

| Winkel | Blick |
|---|---|
| 60 | rechts |
| **66** | **geradeaus** (`PAN_CENTER`, kalibriert) |
| 90 | ca. 18° links |
| 150 | weit links. Ab ca. 130 ist der eigene Reifen unten im Bild |

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

### ⚠️ Kamerakopf ist mechanisch instabil

Der Kamerakopf (Pan/Tilt-Servos mit Kamera) ist **mechanisch nicht stabil**:
- **Kabel im Weg:** Das Flachbandkabel der Kamera und die Servokabel verschieben sich, wenn sich der Kopf oder das Auto dreht. Sie können sich am Kopf verhaken und ihn **verkippen**. Dann ist das Bild schief (Roll), z. B. laufen Laminatfugen schräg durchs Bild.
- **Verdrehter Nullpunkt:** Bei Pan 90 schaut der Kopf ~18° nach links (kalibriert: geradeaus = Pan 66). Das kann sich durch Kabelzug, Stöße oder Servo-Spiel **wieder ändern**.
- **Servo-Spiel:** Je nachdem, aus welcher Richtung der Servo einen Winkel anfährt, steht er minimal anders.

**Folgen:**
- `PAN_CENTER` (Abschnitt Pan) gilt nur, solange der Kopf nicht verrutscht. **Vor jeder Session mit Ausrichten/Parken kurz prüfen:** Blatt gerade vor das Auto legen, `python3 align_exercise_1.py rechts 0` (Trockenlauf). Liegt das Blatt nicht bei ~0°, neu kalibrieren (`calibrate_pan.py`).
- Ein schiefes Bild (Roll) stört die Grün-Erkennung kaum, verfälscht aber Abstandsschätzungen über `pos_y` und das Ablesen des toten Winkels.

**Abhilfe (mechanisch):**
- Kabel mit etwas **Spiel** und so verlegen, dass sie beim Schwenken nicht am Kopf ziehen oder hängen bleiben. Mit Kabelbinder oder Klebeband als Zugentlastung am Chassis fixieren.
- Schrauben der Servo-Arme prüfen.
- Nach dem Umbau `calibrate_pan.py` erneut ausführen.

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
| `align_exercise_1.py` | Blatt suchen und ausrichten | `python3 align_exercise_1.py [rechts\|links] [speed=2000]` (speed 0 = Trockenlauf) |
| `park_exercise_1.py` | Hinfahren und parken (vorher ausrichten) | `python3 park_exercise_1.py [speed=1500]` |
| `mission_exercise_1.py` | Alles: umschauen, suchen, ausrichten, parken | `python3 mission_exercise_1.py [dreh=2000] [fahr=1500]` (0 = Trockenlauf) |
| `calibrate_pan.py` | Pan-Nullpunkt kalibrieren | `python3 calibrate_pan.py 70 95 5` |
| `ground_calibration.py` | Bodenmodell für Tilt 110 | `python3 ground_calibration.py messen <cm> \| auswerten \| reset` |
| `pulse_calibration.py` | Strecke kurzer Fahrimpulse messen | `python3 pulse_calibration.py [dauer=0.16] [anzahl=3]` |

Ausführliche Erklärungen mit Aufgaben: [docs/exercises/](exercises/README.md)

### Grün-Erkennung (`cv_exercise_1.py`)
- Ablauf: Bild (640×480) → HSV → `inRange` → Morphologie (Öffnen/Schließen) → größte Kontur → Schwerpunkt
- **HSV-Bereich:** H 35–95, **S ≥ 35**, V ≥ 40 (OpenCV-Skala H 0–179). S war ursprünglich 60, bei Kunstlicht hat das Blatt aus 150 cm aber nur S ~48.
- **Mindestfläche:** 0,05 % des Bildes (154 Pixel)
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
- Geschwindigkeit: Speed 1500 → ~50 cm in 1 s. Bei kurzen Impulsen gehen ~0,12 s für das Anfahren verloren (siehe Parken).
- Das Auto driftet beim Geradeausfahren leicht nach links.

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

### Zentrale Konfiguration (`pi/car_config.py`)
Kalibrierwerte, die mehrere Skripte brauchen, stehen nur an **einer** Stelle:

| Wert | Bedeutung | Stand |
|---|---|---|
| `PAN_CENTER` | Pan-Wert für „Kamera schaut geradeaus“ | **66** (kalibriert 2026-11-22) |
| `TILT_SEARCH` | Tilt zum Suchen | 90 |
| `TILT_NEAR` | Tilt für den Nahbereich | 110 |

### Pan kalibrieren (`calibrate_pan.py`)
1. Das grüne Blatt **exakt gerade vor das Auto** legen (Blattmitte auf der Längsachse, 50–100 cm entfernt).
2. `python3 calibrate_pan.py 70 95 5` ausführen.
3. Das Skript misst bei jedem Pan-Wert den Winkel zum Blatt und bestimmt per linearer Regression den Pan-Wert für 0°.
4. Den Wert als `PAN_CENTER` in `pi/car_config.py` eintragen und auf den Pi kopieren.

Kalibrierung 2026-11-22 (Blatt exakt vor dem Auto, Tilt 90):

| Pan | Blatt liegt bei |
|---|---|
| 65 | −0,7° |
| 70 | +3,2° |
| 75 | +7,4° |
| 80 | +11,9° |
| 85 | +16,2° |
| 90 | +17,9° |
| 95 | +19,7° |
| 100 | +21,5° |

Nulldurchgang zwischen 65 und 70 → **66**. Ab Pan 90 wird die Kurve flacher, weil das Blatt dort an den rechten Bildrand stößt und abgeschnitten wird. Deshalb wird nur der lineare Bereich 65–85 verwendet (die Regression über alle Werte ergab 63,9). Kontrolle bei Pan 66: Blatt bei −0,5°.

### Ausrichten (`align_exercise_1.py`)
- Testlauf 2026-11-22: Blatt ~115° rechts hinter dem Auto, nach 7 Suchschritten gefunden, nach 2 Korrekturen ausgerichtet (+2,8°).
- **Achtung:** Dieser Lauf lief noch mit Pan 90. Wegen des verdrehten Kamerakopfs (Pan 90 = ~18° links) zeigte das Auto danach deutlich rechts am Blatt vorbei. Seitdem nutzt das Skript `PAN_CENTER`.

### Ausrichten: Robustheit (Stand 2026-11-22)
- Form- und Horizont-Filter `looks_like_sheet`: Blatt muss ≥ 1,5× so breit wie hoch sein und mit der Unterkante unter y = 72 (15 %) liegen. 25 % war zu streng, weil der wacklige Kopf den Horizont verschiebt.
- Blatt kurz weg → erst zweites Foto, dann dort suchen, wo es zuletzt war.
- Toleranz 4°: Der kürzeste Drehimpuls (0,08 s) dreht ~8°, mit 3° pendelte das Auto.

### Parken (`park_exercise_1.py`)
- Getestet 2026-11-22 aus 100 und 150 cm: Das Auto steht auf dem Blatt, Abweichung längs 4–6 cm.
- Ablauf: Tilt 90, 0,4-s-Impulse → bei `pos_y > 0,6` oder Blatt unten am Rand Tilt 110 → 0,2-s-Impulse → Vorderkante am unteren Bildrand → Abstand der **Hinterkante** per Bodenmodell → Rest blind fahren.
- `rest_cm = d_hinterkante − 21/2 + 7,75`, Rückfallebene `5,4 + 21/2 + 7,75` (erster Entwurf hatte hier einen Vorzeichenfehler).
- `rest_s = rest_cm / 50 + 0,12` (**Anfahrverzug 0,12 s**: 0,16 s fahren ≈ 2 cm, nicht 8 cm).
- Nach jedem Impuls 0,8 s warten und ein Bild verwerfen (Bewegungsunschärfe bei Kunstlicht).
- Blatt-Lage: A4 **quer** zur Fahrtrichtung (21 cm in Fahrtrichtung). Liegt es hochkant: `BLATT_LAENGE_CM = 29.7`.
- Das Blatt muss **fixiert** sein (Klebeband), sonst können die Räder es wegschieben.

### Mission (`mission_exercise_1.py`)
- Alles in einem: Kopf schwenken (0°, ±25°, ±45° → ca. ±72° Sicht), suchen, ausrichten, anfahren, parken. Dauer ~25 s.
- `python3 mission_exercise_1.py 0` = Trockenlauf (nur umschauen).
- Pan außerhalb 65–85 ist nicht kalibriert, die Winkel aus dem Kopfschwenk sind dort nur grob. Für die Drehrichtung reicht es.

### Weitere Werkzeuge
- `pulse_calibration.py [dauer] [anzahl]`: misst mit der Hinterkante, wie weit ein kurzer Fahrimpuls wirklich fährt. Das Auto muss so stehen, dass die Hinterkante bei Tilt 110 deutlich mehr als 7 cm entfernt ist, sonst verschwindet sie nach einem Impuls im toten Winkel.

### Boden-Kalibrierung (`ground_calibration.py`), Tilt 110
- Methode: Vordere Blattkante auf 5 / 10 / 20 cm ab Autokante legen und die Bildzeile in der **Bildmitte** messen. Modell `d = h / tan(α + atan((y − 240)/f))`.
- Messpunkte: 5 cm → y 402, 10 cm → y 250, 20 cm → y 133 (Linse 1,75 cm hinter der Autokante).
- Höhe und Brennweite sind aus Nahbereichs-Punkten **nicht trennbar**. Deshalb f = 634 px fest (durch Übung 4 bestätigt). Ergebnis: **h = 5,2 cm, Neigung 23,0°, RMS 0,05 cm**. Grob mit dem Lineal gemessen waren „etwa 7 cm“.
- **Toter Winkel: 5,4 cm ab Linse = 3,7 cm ab Autokante.** Robust: 2,4–3,7 cm für jede plausible Höhe.
- Werte in `car_config.py`: `CAMERA_HEIGHT_CM`, `TILT_NEAR_PITCH_DEG`, `DEAD_ZONE_FROM_LENS_CM`, `LENS_BEHIND_FRONT_CM`.
- Abmessungen: Auto ~19 cm lang, Linse 7,75 cm vor der Automitte.

### Grün-Erkennung aus der Ferne
- Aus 150 cm ist das Blatt ein ~116 × 17 Pixel großer Streifen (0,1 % des Bildes) mit blasserer Farbe (S ~96).
- Deshalb: Öffnen 3×3, Schließen 15×5 (überbrückt Reflex-Lücken), Mindestfläche 0,05 %.

### Licht
- Abends bei Kunstlicht meldet die Kamera ~57 Lux, 2430 K, Gain 8 (Maximum) und 33 ms Belichtung. Folgen: Bewegungsunschärfe, Rauschen, blasse Farben.
- Gegenmaßnahmen im Code: Nach Bewegungen warten (0,4–0,8 s) und ein Bild verwerfen, bei „kein Blatt“ neu fotografieren, Sättigungsgrenze S ≥ 35.
- Metadaten auslesen: `cam.capture_metadata()` → `ExposureTime`, `AnalogueGain`, `Lux`, `ColourTemperature`.
- Farbwerte nie auf Debug-Overlays messen (Zeichnungen, Kompression), sondern auf Rohbildern.
