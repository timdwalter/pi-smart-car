# SmartCar – Projektübersicht

> - Bedienung, Hardware-Belegung, Befehle: **[docs/OPERATIONS_MANUAL.md](docs/OPERATIONS_MANUAL.md)**
> - Übungen (z. B. für eine Hackerschool): **[docs/exercises/](docs/exercises/README.md)**
> - **Lehrbuch** (Einstieg, alle Übungen mit Lösungen, Projektaufgaben, Glossar als eine HTML-Datei): `python tools/build_lehrbuch.py` → `dist/SmartCar_Lehrbuch.html`, Rahmentexte in [docs/lehrbuch/](docs/lehrbuch/)
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
- **Kamera:** OV5647 (Pi Camera v1, picamera2) auf Pan/Tilt-Servos
- **Weitere Sensoren:** Ultraschall, Line-Tracking (Standard im Kit)
- **PCB-Version:** unbekannt, wird per SSH auf dem Pi geprüft
- **Stand:** zusammengebaut, Freenove-App (Server/Client) funktioniert, Kamera läuft

## Architektur
- Bilderkennung und Steuerlogik laufen **direkt auf dem Pi**, autonom und ohne PC.
- Entwickelt wird auf dem **Windows-PC (PyCharm)**. Der Code wird per **SSH/scp** auf den Pi kopiert und dort ausgeführt.

## Testumgebung
- Anfangs auf dem Schreibtisch aufgebockt (Räder frei).
- **Seit 2026-11-22 auf dem Boden** (helles Laminat). Motortests bewegen das Auto jetzt wirklich, vorher immer nachfragen!

## Offene Punkte
- [x] IP, User und Passwort des Pi in `.env` eintragen (User: `pi`, Hostname: `raspberrypi`)
- [ ] Optional: SSH-Key-Login einrichten
- [x] Pfad des Freenove-Codes: `/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server`
- [ ] PCB-Version ermitteln: keine `params.json` vorhanden, also wohl die ältere Code-Version (vor PCB V2). Bei `Motor.py` prüfen.
- [ ] Eigene Dateien im Server-Ordner sichten: `Christian.py`, `Mirwais.py`, `image_rec.py`, `image_rec_1.py`, `test.py`, `server_ui.py` (stammen nicht von Freenove)

## Statuslog
Details zu allen Punkten: [docs/OPERATIONS_MANUAL.md](docs/OPERATIONS_MANUAL.md)
- 2026-11-22: SSH-Zugang über `tools/pi.py` + `.env` ✅
- 2026-11-22: Motortest ✅ (Räder drehen; Motorschalter separat, Akku war tiefentladen)
- 2026-11-22: Tailscale eingerichtet (`smartcar`, `100.77.136.52`) ✅
- 2026-11-22: Akkus geladen (8,04 V) ✅
- 2026-11-22: Kamera-Testbild ✅
- 2026-11-22: Servo-Belegung per Scan ermittelt ✅ (Kanal 0 = Tilt, Kanal 1 = Pan; Tilt 90 = Suchen, 110 = Nahbereich; geradeaus = Pan 66, nicht 90!)
- 2026-11-22: Grün-Erkennung `pi/cv_exercise_1.py` erkennt das Blatt ✅ (HSV H 35–95, Blatt ist blaugrün)
- 2026-11-22: Fahr-Übung `pi/drive_exercise_1.py` (vor/zurück) ✅
- 2026-11-22: Dreh-Übung `pi/turn_exercise_1.py`: 90° per visueller Odometrie (kein Gyro vorhanden), 4 Läufe (87–91° gemessen, real knapp unter 90°) ✅. Bildwinkel nicht exakt kalibriert. Reifen und Laminat lassen die Drehrate stark schwanken (42–62°/s).
- 2026-11-22: Übung 5 `pi/align_exercise_1.py`: Blatt ~115° rechts hinter dem Auto gefunden und ausgerichtet ✅
- 2026-11-22: **Kamerakopf verdreht**: Pan 90 schaut ~18° nach links. Größere Pan-Werte = **links** (vorher falsch dokumentiert). Kalibriert mit `pi/calibrate_pan.py`: **geradeaus = Pan 66** ✅ (zentral in `pi/car_config.py`).
- 2026-11-22: **Kamerakopf mechanisch instabil**: Kabel verschieben sich beim Drehen, verhaken sich am Kopf und verkippen ihn (schiefes Bild). `PAN_CENTER` vor jeder Session prüfen. Kabelführung bzw. Zugentlastung verbessern (offen).
- 2026-11-22: Fahrgeschwindigkeit gemessen: Speed 1500 für 1,0 s ≈ **50 cm** (inkl. Anfahren).
- 2026-11-22: Boden-Kalibrierung (`pi/ground_calibration.py`): toter Winkel 3,7 cm ab Autokante, Kamerahöhe 5,2 cm, Neigung 23° bei Tilt 110 ✅
- 2026-11-22: Grün-Erkennung für Fernbereich verbessert (150 cm): Öffnen 3×3, Schließen 15×5, Mindestfläche 0,1 % ✅
- 2026-11-22: Übung 6 `pi/park_exercise_1.py` kalibriert (50 cm/s, toter Winkel 5,4 cm ab Linse, Linse 7,75 cm vor Mitte, Blatt 21 cm quer).
- 2026-11-22 (abends, Kunstlicht): Übung 5 robuster gemacht: Form-/Horizont-Filter, zweites Foto bei Verlust, Suche Richtung „zuletzt gesehen“, Toleranz 4°. Grün-Erkennung S ≥ 35 (Kunstlicht), Mindestfläche 0,05 %.
- 2026-11-22: **Übung 6 getestet** ✅: aus 100 und 150 cm steht das Auto auf dem Blatt, 4–6 cm Abweichung längs. Gefunden und behoben: Vorzeichenfehler in der Blindstrecke, Anfahrverzug 0,12 s, zu später Tilt-Wechsel, Bewegungsunschärfe, Reflex-Fehlalarm. Reststrecke jetzt über die Hinterkante des Blattes (Bodenmodell).
- 2026-11-22: **Übung 7 `pi/mission_exercise_1.py`: Stufe 1 komplett** ✅ Umschauen per Kopfschwenk, suchen, ausrichten, anfahren, parken in ~25 s. 2 von 2 Läufen erfolgreich (Blatt bei +42° bzw. +61°, ~150 cm). `align()` und `park()` sind jetzt wiederverwendbare Funktionen.
- 2026-11-22: **Lehrbuch** für IoT-Hacking-Kollegen: `tools/build_lehrbuch.py` baut aus Kollegen-Anleitung, Übungen, Operations Manual und Rahmentexten (`docs/lehrbuch/`: Vorwort, Auto im Überblick, Kapitel-Einleitungen, Projektaufgaben, Glossar) eine HTML-Datei mit Inhaltsverzeichnis und eingebetteten Bildern ✅. Hacker-School-Fassung und Vortrag sind zurückgestellt.
- Doku: neue Übung 5b `docs/exercises/calibration_exercise_1.md` (Kalibrierung mit allen Umwegen)
- Freenove-Repo auf dem Pi hat lokale Änderungen: `test.py` (Motortest umgebaut), `ADC.py` (`calcPowerLevel()`)

## Weitere offene Punkte
- [ ] **Vor Zugriff durch Kollegen:** Pi ins Gast- oder IoT-WLAN umziehen. Begründung: `pi` hat sudo ohne Passwort und das Passwort ist bekannt. Damit wären das WLAN-Passwort im Klartext (`/etc/NetworkManager/system-connections/`) und das ganze Heimnetz über den Pi erreichbar.
- [ ] Kabel am Kamerakopf mit Spiel verlegen und Zugentlastung anbringen, danach `calibrate_pan.py` erneut ausführen
- [ ] Akku laden (zuletzt ~7,0 V), danach Parkgenauigkeit mit vollem Akku prüfen (Anfahrverzug/Speed sind bei ~7 V gemessen)
- [ ] Bodenmodell mit Punkten bis ~30 cm erweitern (Hinterkante liegt beim Parken bei 21–30 cm)
- [ ] Optional: Video der Mission in `docs/exercises/` verlinken
- [ ] Spätere Bodenumgebung klären: Untergrund, Blattgröße (A4?), Hindernisse, ob das Blatt außer Sicht liegen kann

## Ideen für später
- **Draufsicht-Kamera** über dem Fahrbereich, remote über Tailscale ansehbar. Kamera und Lagerort des Autos sind noch offen. Details: [docs/ADMIN_REMOTE.md](docs/ADMIN_REMOTE.md#5-draufsicht-kamera-geplant)

## Vorgehen
1. ✅ **Bestandsaufnahme per SSH:** Python, picamera2, OpenCV und Freenove-Treiber prüfen.
2. ✅ **Smoke-Test:** Kamerabild aufnehmen, Motoren kurz ansteuern.
3. ✅ **Grün-Erkennung (OpenCV, HSV):** Debug-Bilder speichern und am PC ansehen.
4. ✅ **Fahrlogik als Zustandsautomat:** `pi/mission_exercise_1.py` (Stufe 1 erreicht)
   - `SUCHEN`: auf der Stelle drehen, bis Grün im Bild ist
   - `AUSRICHTEN`: drehen, bis das Blatt horizontal mittig im Bild liegt
   - `ANFAHREN`: geradeaus fahren und dabei nachkorrigieren
   - `PARKEN`: wenn das Blatt unten aus dem Bild verschwindet, noch eine kalibrierte Strecke nachfahren und stoppen
