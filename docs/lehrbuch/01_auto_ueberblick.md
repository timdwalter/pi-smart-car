# Das Auto im Überblick

Dieses Kapitel fasst zusammen, was vor der ersten Übung bekannt sein sollte: woraus das Auto besteht, was ihm fehlt, wie Code auf das Auto kommt und welche Konventionen im ganzen Projekt gelten. Alle Details, Befehle und Messwerte stehen im Betriebshandbuch im Anhang.

## Aufbau

| Baustein | Was es ist | Wofür es gebraucht wird |
|---|---|---|
| **Raspberry Pi 4** | Der Rechner auf dem Auto, Debian 12, Python 3.11 | Bilderkennung und Steuerlogik laufen hier, ohne PC |
| **Kamera OV5647** | Pi Camera v1 auf einem Pan/Tilt-Kopf mit zwei Servos | Der wichtigste Sensor: Erkennen, Drehwinkel messen, Abstände schätzen |
| **4 Motoren** | Vier angetriebene Räder ohne Lenkung | Fahren und auf der Stelle drehen (Panzerlenkung) |
| **PCA9685** | PWM-Baustein am I2C-Bus (`0x40`) | Steuert Motoren und Servos |
| **ADS7830** | Analog-Digital-Wandler am I2C-Bus (`0x48`) | Misst die Akkuspannung |
| **Ultraschall** | Abstandssensor vorne | Hindernisse, Plausibilitätschecks |
| **2× 18650** | Li-Ion-Akkus in Reihe, voll 8,4 V | Strom für Pi und Motoren (zwei getrennte Schalter!) |

## Was dem Auto fehlt

Mindestens so wichtig wie die vorhandene Hardware ist die **fehlende**:

- **Kein Gyroskop, keine IMU.** Wie weit sich das Auto gedreht hat, muss anders gemessen werden. Übung 4 löst das mit der Kamera (visuelle Odometrie).
- **Keine Radencoder.** Gefahrene Strecken lassen sich nur über **Geschwindigkeit × Zeit** schätzen, was durch Akkustand, Boden und Anfahrverzug ungenau wird (Übung 5b, 6).
- **Keine Lenkung.** Kurven und Drehungen entstehen durch unterschiedlich schnelle Räder. Die Reifen rutschen dabei, die Drehrate schwankt zwischen 42 und 62 °/s.
- **Kein Bildschirm.** Der Pi läuft „headless“. Alle Skripte speichern ihre Ergebnisse als Bilder, die auf den PC geholt und dort angesehen werden.

## Wie Code auf das Auto kommt

```
 PC (Windows, PyCharm)                         Raspberry Pi auf dem Auto
 ─────────────────────                         ─────────────────────────
 pi/<skript>.py  ── tools/pi.py put ──▶        ~/smartcar/<skript>.py
                 ── tools/pi.py run ──▶        python3 <skript>.py  → Motoren, Kamera
 debug/<bild>.jpg ◀── tools/pi.py get ──       ~/smartcar/debug/<bild>.jpg
                    (SSH über Tailscale)
```

Entwickelt wird am eigenen Rechner. `tools/pi.py` kopiert Dateien per SSH auf den Pi, startet sie dort und holt Debug-Bilder zurück. Die Zugangsdaten liest das Werkzeug aus der lokalen `.env`.

Der **Freenove-Originalcode** auf dem Pi (`~/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server`) wird nicht verändert, sondern nur importiert. Eigener Code liegt in `~/smartcar/`.

## Konventionen im ganzen Projekt

Einige Richtungen sind beim echten Auto anders, als man erwarten würde. Sie gelten in allen Skripten und Übungen:

| Größe | Konvention |
|---|---|
| **Pan** (Servo-Kanal `"1"`) | **Größere Werte = nach links.** Geradeaus ist **Pan 66**, nicht 90 (Kamerakopf verdreht). Etwa 0,85° pro Einheit. |
| **Tilt** (Servo-Kanal `"0"`) | Größere Werte = nach unten. **90** zum Suchen, **110** für den Nahbereich. |
| **`offset_x`** | Lage des Blattes im Bild: −1 = ganz links, 0 = Mitte, +1 = ganz rechts |
| **`pos_y`** | 0 = oberer Bildrand (weit weg), 1 = unterer Bildrand (nah) |
| **Winkel** | Positive Grad = **rechts** vom Auto |
| **Motoren** | `setMotorModel(vorne_links, hinten_links, vorne_rechts, hinten_rechts)`, −4095 … 4095 |

## Zentrale Kalibrierwerte

Werte, die mehrere Skripte brauchen, stehen nur in **`pi/car_config.py`**. Skripte importieren sie von dort, statt Zahlen fest einzutragen.

| Wert | Stand | Bedeutung |
|---|---|---|
| `PAN_CENTER` | 66 | Pan-Wert für „Kamera schaut geradeaus“ |
| `TILT_SEARCH` / `TILT_NEAR` | 90 / 110 | Suchen / Nahbereich |
| `CAMERA_HEIGHT_CM` | 5,2 | Linsenmitte über dem Boden |
| `TILT_NEAR_PITCH_DEG` | 23,0 | Neigung der Kamera bei Tilt 110 |
| `DEAD_ZONE_FROM_LENS_CM` | 5,4 | Toter Winkel vor der Linse |
| `LENS_BEHIND_FRONT_CM` | 1,75 | Linse hinter der Vorderkante |

Weitere Kennzahlen, die immer wieder auftauchen: Brennweite **f ≈ 634 px** bei 640 × 480, Fahrgeschwindigkeit **≈ 50 cm/s** bei Speed 1500, **Anfahrverzug 0,12 s**.

> ⚠️ Der Kamerakopf ist mechanisch instabil: Kabel ziehen am Kopf und können ihn verdrehen. Vor jeder Session mit Ausrichten oder Parken lohnt sich ein kurzer Check von `PAN_CENTER` (siehe Übung 5 und Betriebshandbuch).
