# Admin-Anleitung: Remote-Zugriff, Kollegen und Draufsicht-Kamera

Nur für Tim (Besitzer von Tailnet und Pi). Den Kollegen schickst du **[KOLLEGEN_ANLEITUNG.md](KOLLEGEN_ANLEITUNG.md)**.

Stand: 2026-11-22

## 1. Überblick

| Was | Wert |
|---|---|
| Tailscale-Gerätename | `smartcar` |
| Tailscale-IP | `100.77.136.52` |
| Tailscale-Version | 1.104.7 |
| Linux-User | `pi` (sudo ohne Passwort) |
| Freenove-Code auf dem Pi | `/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server` |
| Admin-Konsole | https://login.tailscale.com/admin/machines |

Falls der Pi aus dem Tailnet fliegt: lokal per SSH auf den Pi und `sudo tailscale up --hostname=smartcar` ausführen, dann den Login-Link im Browser öffnen.

---

## 2. ⚠️ Bevor Kollegen Zugriff bekommen

`pi` hat **sudo ohne Passwort**, und das Passwort ist bekannt. Wer auf dem Pi eingeloggt ist, kann deshalb:
- das **WLAN-Passwort im Klartext** auslesen (`/etc/NetworkManager/system-connections/*.nmconnection` oder `sudo nmcli -s connection show <WLAN>`),
- vom Pi aus **alle anderen Geräte im lokalen Netz** erreichen. „Share“ begrenzt nur den Zugriff *auf den Pi*, nicht was man *vom Pi aus* erreicht.

**Checkliste:**
- [ ] Den Pi in ein **Gast- oder IoT-WLAN** hängen, das vom Heimnetz getrennt ist (z. B. FritzBox-Gastzugang). Das gilt auch für den späteren Lagerort, siehe Abschnitt 5.
- [ ] Optional: `sudo` nur mit Passwort, bzw. eigene User ohne `sudo` für Kollegen.

WLAN per SSH umstellen: `sudo nmcli device wifi connect "<SSID>" password "<PW>"`.
**Vorsicht:** Danach ist der Pi nur noch über das neue Netz bzw. über Tailscale erreichbar. Tailscale funktioniert nach dem Wechsel automatisch weiter. Den Wechsel am besten vor Ort machen, falls etwas schiefgeht.

---

## 3. Kollegen Zugriff geben

### Gerät teilen (empfohlen)
1. In der Admin-Konsole bei `smartcar` das **„…“-Menü** öffnen und **„Share…“** wählen.
2. Eine Einladung per E-Mail schicken oder den **Einladungslink** kopieren.
3. Dem Kollegen schicken:
   - den Einladungslink
   - **[KOLLEGEN_ANLEITUNG.md](KOLLEGEN_ANLEITUNG.md)**
   - das `pi`-Passwort, getrennt und nicht im selben Chat wie die IP
   - Zugang zum Repo, sobald ein gemeinsamer Ort feststeht (aktuell nur lokal)

**Zugriff entziehen:** im selben „Share“-Menü die Freigabe widerrufen. Wenn jemand das Passwort nicht mehr haben soll, musst du zusätzlich das `pi`-Passwort ändern (`passwd` auf dem Pi). Das betrifft dann alle.

### Was ein Kollege mit „Share“ sieht und darf
- ✅ Er erreicht den Pi und kann dort alles, was `pi` darf.
- ❌ Er sieht keine anderen Geräte aus deinem Tailnet (z. B. deinen PC).

### Alternative: ins Tailnet einladen
Unter **Settings → Users → Invite** wird der Kollege ein echtes Mitglied des Tailnets. Das lohnt sich erst bei mehreren gemeinsamen Geräten (Auto plus Draufsicht-Kamera). Dann **muss** man über ACLs regeln, wer welche Geräte sieht. Sonst sieht der Kollege auch deine privaten Geräte.

### Später: Tailscale SSH
Mit `sudo tailscale set --ssh` auf dem Pi läuft der Login über das Tailscale-Konto statt über ein Passwort. Damit entfällt das geteilte Passwort, und man sieht in den Logs, wer sich wann verbunden hat. Dafür braucht es eine SSH-Regel in den ACLs.

---

## 4. Repo

Das Repo liegt aktuell **nur lokal** auf Tims PC. Optionen für später:
- privates Repo auf GitHub/GitLab (empfohlen, mit Backup)
- Bare-Repo auf dem Pi (kein externer Dienst, aber kein Backup)

---

## 5. Draufsicht-Kamera (geplant)

**Ziel:** Eine externe Kamera schaut von oben auf den Fahrbereich. So sieht man auch remote, was das Auto tut.

### Offen
- [ ] Kamera ist noch **nicht vorhanden**
- [ ] Der **endgültige Lagerort** des SmartCars ist noch **unklar**. Er bestimmt WLAN, Montage der Kamera und Fahrfläche.

### Geplanter Aufbau
- Die Kamera hängt **über dem Fahrbereich**, nicht am Auto.
- Sie läuft **unabhängig vom Auto-Pi**. Der Pi 4 braucht seine Rechenleistung für die Fahrlogik, und die Kamera soll auch funktionieren, wenn das Auto aus ist oder abstürzt.
- Die Kamera kommt **ins Tailnet** und wird genauso per „Share“ freigegeben wie `smartcar`.

### Hardware-Optionen
| Option | Vorteile | Nachteile |
|---|---|---|
| Altes Handy + IP-Webcam-App | kostet nichts, sofort einsatzbereit | Akku/Netzteil, Halterung, App-abhängig |
| Pi Zero 2 W + Pi-Kamera | gleich verwaltbar wie das Auto (SSH, Tailscale), flexibel | muss gekauft und eingerichtet werden |
| USB-Webcam an einem Rechner vor Ort | einfach | es muss ein Rechner dauerhaft laufen |

### Bonus
Aus der Draufsicht lässt sich **objektiv messen**, ob das Auto mittig auf dem grünen Blatt geparkt hat. Damit lassen sich die Parktests automatisch auswerten.
