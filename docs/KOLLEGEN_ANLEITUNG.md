# SmartCar – Einstieg für IoT-Hacking-Teilnehmer

Diese Anleitung erklärt, wie sich IoT-Hacking-Teilnehmer mit dem SmartCar verbinden und mitentwickeln können, auch von zu Hause aus.

## Worum geht's?

Ein **Freenove 4WD Smart Car** mit einem Raspberry Pi 4 und einer Kamera. Das Ziel von Stufe 1: Das Auto soll **ein grünes Blatt Papier auf dem Boden erkennen, sich dazu drehen, hinfahren und mittig darauf parken**, und zwar vollständig autonom.

Der Code wird am eigenen Rechner geschrieben, per SSH auf den Pi kopiert und dort ausgeführt.

---

## Schritt 1: Tailscale installieren

Der Pi steht nicht im selben Netzwerk wie die Teilnehmer. Die Verbindung läuft deshalb über **Tailscale**, ein privates, verschlüsseltes Netz zwischen Geräten. Es müssen keine Ports freigegeben und keine Router-Einstellungen geändert werden.

1. Tailscale herunterladen: **https://tailscale.com/download** (Windows, Mac, Linux, Handy)
2. Installieren und **mit einem eigenen Konto anmelden**, z. B. mit Google, Microsoft oder GitHub. Das ist kostenlos.

## Schritt 2: Einladung annehmen

Jeder IoT-Hacking-Teilnehmer erhält von Tim einen **Einladungslink** (oder eine E-Mail von Tailscale).

1. Link öffnen
2. Mit demselben Konto wie in Schritt 1 anmelden und **„Accept“** klicken
3. Danach erscheint in der Tailscale-Geräteliste das Gerät **`smartcar`**

Sichtbar ist nur dieses eine Gerät, sonst nichts aus Tims Netz.

## Schritt 3: Verbindung testen

Tailscale muss auf dem eigenen Rechner laufen (Symbol in der Taskleiste: „Connected“). Dann im Terminal oder in der PowerShell:

```
ssh pi@100.77.136.52
```

Das **Passwort** gibt Tim separat heraus. Klappt der Login, ist man auf dem Pi. Mit `exit` geht es wieder zurück.

> Falls `smartcar` als Name nicht funktioniert: einfach die IP `100.77.136.52` verwenden. Die funktioniert immer.

## Schritt 4: Projekt einrichten

1. **Projekt-Repo holen.** Den Ort (Git-Link oder Zip) gibt Tim bekannt.
2. **Python-Umgebung anlegen** (Python 3.11 oder neuer):
   ```
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt      # Windows
   .venv/bin/python -m pip install -r requirements.txt              # Mac/Linux
   ```
3. **Zugangsdaten eintragen:** `.env.example` nach `.env` kopieren und ausfüllen:
   ```
   PI_HOST=100.77.136.52
   PI_USER=pi
   PI_PASSWORD=<Passwort von Tim>
   ```
   Die `.env` bleibt lokal. Sie wird nicht committet und nicht weitergegeben.
4. **Testen:**
   ```
   .venv\Scripts\python.exe tools\pi.py run hostname
   ```
   Die Ausgabe sollte `raspberrypi` sein.

### Nützliche Befehle
| Befehl | Was er tut |
|---|---|
| `tools/pi.py run "<befehl>"` | Befehl auf dem Pi ausführen |
| `tools/pi.py put <lokal> <remote>` | Datei auf den Pi kopieren |
| `tools/pi.py get <remote> <lokal>` | Datei vom Pi holen (z. B. Kamerabilder) |

### Arbeiten mit Claude Code (optional)
Mit Claude Code einfach den Projektordner öffnen. `CLAUDE.md` und `PROJECT.md` werden automatisch gelesen, und Claude kennt damit den aktuellen Stand, die Hardware und die Regeln.

---

## Spielregeln 🚗

1. **Motoren:** Vorher klären, ob das Auto **aufgebockt** ist oder auf dem Boden steht. Remote ist das nicht zu sehen! Im Zweifel bei Tim nachfragen.
2. **Motorbefehle immer zeitlich begrenzen** und im `finally` stoppen:
   ```python
   try:
       motor.setMotorModel(2000, 2000, 2000, 2000)
       time.sleep(1)
   finally:
       motor.setMotorModel(0, 0, 0, 0)
   ```
3. **Akku vor dem Fahren prüfen.** Unter ca. 6,5 V reicht die Kraft für die Motoren nicht.
4. **Freenove-Originalcode nicht verändern** (`~/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/`). Nur importieren, eigener Code kommt in einen eigenen Ordner.
5. **Keine Änderungen an System, Tailscale oder WLAN** ohne Absprache mit Tim. Sonst sperren sich womöglich alle aus.
6. **Kurz Bescheid geben**, wer gerade mit dem Auto arbeitet. Zwei Leute gleichzeitig an den Motoren gibt Chaos.

---

## Probleme?

| Problem | Lösung |
|---|---|
| `ssh` hängt oder Timeout | Läuft Tailscale lokal („Connected“)? Ist der Pi eingeschaltet? Tim fragen. |
| `smartcar` taucht nicht auf | Einladung noch nicht angenommen, oder mit einem anderen Konto angemeldet |
| Motoren drehen sich nicht | Motorschalter am Auto aus oder Akku leer. Das geht nur vor Ort, Tim fragen. |
| `Can't open /dev/mem` / Segfault bei `test.py` | Das Skript braucht `sudo`: `sudo python3 test.py Motor` |

Bei allen anderen Fragen: bei Tim melden.
