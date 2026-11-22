# SmartCar – Projektübersicht

> - Neue Mitentwickler: **[docs/KOLLEGEN_ANLEITUNG.md](docs/KOLLEGEN_ANLEITUNG.md)** (zum Verschicken)
> - Admin (Tailscale, Kollegen freischalten, Sicherheit, Draufsicht-Kamera): **[docs/ADMIN_REMOTE.md](docs/ADMIN_REMOTE.md)**

## Setup für neue Entwickler
1. Repo klonen
2. Tailscale installieren und Zugriff auf das Gerät `smartcar` bekommen (Share/Einladung durch den Besitzer)
3. `python -m venv .venv` und `.venv/Scripts/python.exe -m pip install -r requirements.txt` (unter Linux/Mac `.venv/bin/python`)
4. `.env.example` nach `.env` kopieren, `PI_HOST=smartcar`, `PI_USER=pi` und das Passwort eintragen
5. Test: `.venv/Scripts/python.exe tools/pi.py run hostname` → `raspberrypi`

## Ziel

### Stufe 1
Das Auto soll autonom:
1. ein **grünes Blatt Papier** auf dem Boden erkennen,
2. sich dazu **ausrichten** (drehen),
3. darauf **zufahren**,
4. **mittig auf dem Blatt parken**, also mit allen Rädern ungefähr mittig auf dem Blatt anhalten.

## Hardware
- **Auto:** Freenove 4WD Smart Car Kit for Raspberry Pi
- **Rechner:** Raspberry Pi 4
- **Kamera:** Raspberry-Pi-Kamera (Flachbandkabel, picamera2) auf Pan/Tilt-Servos
- **Weitere Sensoren:** Ultraschall, Line-Tracking (Standard im Kit)
- **PCB-Version:** unbekannt, wird per SSH auf dem Pi geprüft
- **Stand:** zusammengebaut, Freenove-App (Server/Client) funktioniert, Kamera läuft

## Architektur
- Bilderkennung und Steuerlogik laufen **direkt auf dem Pi**, autonom und ohne PC.
- Entwickelt wird auf dem **Windows-PC (PyCharm)**. Der Code wird per **SSH/scp** auf den Pi kopiert und dort ausgeführt.

## Testumgebung
- Vorerst **auf dem Schreibtisch aufgebockt**: Die Räder drehen frei, das Auto kann nicht wegfahren.
  - Damit lassen sich Kamera, Erkennung und Motoransteuerung testen.
  - Echtes Hinfahren und Parken wird erst später auf dem Boden getestet.

## Offene Punkte
- [x] IP, User und Passwort des Pi in `.env` eintragen (User: `pi`, Hostname: `raspberrypi`)
- [ ] Optional: SSH-Key-Login einrichten
- [x] Pfad des Freenove-Codes: `/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server`
- [ ] PCB-Version ermitteln: keine `params.json` vorhanden, also wohl die ältere Code-Version (vor PCB V2). Bei `Motor.py` prüfen.
- [ ] Eigene Dateien im Server-Ordner sichten: `Christian.py`, `Mirwais.py`, `image_rec.py`, `image_rec_1.py`, `test.py`, `server_ui.py` (stammen nicht von Freenove)

## Pi-Umgebung (Stand 2026-11-22)
- Raspberry Pi 4 Model B Rev 1.1, Python 3.11.2
- OpenCV 4.6.0 und picamera2 sind systemweit installiert
- Freenove-Repo auf dem Pi ist ein git-Checkout. Lokal geändert: `test.py` (Motortest umgebaut) und `ADC.py` (`calcPowerLevel()`: Akku 5,6–8,4 V → 0–1)
- **Motor-API** (aus `test.py`): `Motor().setMotorModel(fl, bl, fr, br)`, Werte etwa −4095…4095, Vorzeichen = Richtung
  - vorwärts `(2000,2000,2000,2000)`, auf der Stelle drehen `(-x,-x,x,x)` = links bzw. `(x,x,-x,-x)` = rechts, Stopp `(0,0,0,0)`
- Weitere APIs: `Servo().setServoPwm('0'|'1', winkel)` (Kamera-Pan/Tilt, 90 = Mitte), `Ultrasonic().get_distance()` (cm), `Adc().recvADC(2)*3` = Akkuspannung
- Testaufruf auf dem Pi: `sudo python3 test.py Motor|Servo|Ultrasonic|Led|ADC|Buzzer|Infrared|Rotate`
  - **`sudo` ist nötig**, weil die LED-Lib (`rpi_ws281x`) `/dev/mem` braucht. Ohne `sudo` gibt es einen Segfault beim Import. `sudo` geht ohne Passwort.
  - Motoransteuerung allein (`from Motor import Motor`) läuft auch ohne `sudo`.
- 2026-11-22: Motortest per SSH erfolgreich ausgeführt, **Räder drehen sich** ✅
  - Motorstrom braucht einen separaten Schalter am Auto. Ohne diesen misst der ADC 0 V und die Motoren bewegen sich nicht.
  - Akku war mit ~4,2 V (unter Last ~3,9 V) **tiefentladen**, normal sind 6,5–8,4 V. Akkus laden bzw. prüfen. Vor Fahrtests immer die Akkuspannung messen.
- **Tailscale** 1.104.7 installiert (2026-11-22), Hostname im Tailnet: `smartcar`, Tailscale-IP `100.77.136.52`. Verbunden, der Windows-PC ist ebenfalls im Tailnet. SSH über `smartcar` getestet ✅. Login über `sudo tailscale up --hostname=smartcar`.
  - Fernzugriff von außerhalb: `.env` → `PI_HOST` auf die Tailscale-IP (100.x.y.z) oder `smartcar` (MagicDNS) setzen. Der PC muss dafür ebenfalls in Tailscale sein.
- SSH-Helfer: `.venv/Scripts/python.exe tools/pi.py run "<befehl>"` bzw. `put`/`get`
- [ ] **Vor Zugriff durch Kollegen:** Pi ins Gast- oder IoT-WLAN umziehen. Begründung: `pi` hat sudo ohne Passwort und das Passwort ist bekannt. Damit wären das WLAN-Passwort im Klartext (`/etc/NetworkManager/system-connections/`) und das ganze Heimnetz über den Pi erreichbar.
- [ ] Spätere Bodenumgebung klären: Untergrund, Blattgröße (A4?), Hindernisse, ob das Blatt außer Sicht liegen kann

## Ideen für später
- **Draufsicht-Kamera** über dem Fahrbereich, remote über Tailscale ansehbar. Kamera und Lagerort des Autos sind noch offen. Details: [docs/ADMIN_REMOTE.md](docs/ADMIN_REMOTE.md#5-draufsicht-kamera-geplant)

## Vorgehen
1. **Bestandsaufnahme per SSH:** Python, picamera2, OpenCV und Freenove-Treiber prüfen.
2. **Smoke-Test:** Kamerabild aufnehmen, Motoren kurz ansteuern.
3. **Grün-Erkennung (OpenCV, HSV):** Debug-Bilder speichern und am PC ansehen.
4. **Fahrlogik als Zustandsautomat:**
   - `SUCHEN`: auf der Stelle drehen, bis Grün im Bild ist
   - `AUSRICHTEN`: drehen, bis das Blatt horizontal mittig im Bild liegt
   - `ANFAHREN`: geradeaus fahren und dabei nachkorrigieren
   - `PARKEN`: wenn das Blatt unten aus dem Bild verschwindet, noch eine kalibrierte Strecke nachfahren und stoppen
