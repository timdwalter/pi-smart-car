# CLAUDE.md – Hinweise für AI-Sessions

Projektkontext, Hardware, Ziel und aktueller Stand stehen in:
@PROJECT.md

Bedienung, Hardware-Belegung (Motoren, Servos, Kamera, Akku) und bekannte Stolperfallen:
@docs/OPERATIONS_MANUAL.md

- Neue Übungsskripte in `pi/` bekommen eine passende Erklärung in `docs/exercises/<name>.md` und einen Eintrag in `docs/exercises/README.md`. Aufbau jeder Datei: **Lernziele**, dann **Teil A – Lecture** (Problem, Theorie Schritt für Schritt, Code, Bilder und Ergebnisse echter Testläufe), dann **Teil B – Exercise** (Sicherheit, Ausprobieren, Aufgaben, Lösungen in `<details>`). Bilder aus Testläufen dauerhaft in `docs/exercises/images/` ablegen. Die Texte sind neutral formuliert, ohne „du“.
- Neue Erkenntnisse zur Bedienung oder Hardware (gemessene Werte, Belegungen, Fehler und Lösungen) im Operations Manual eintragen, den Projektfortschritt im Statuslog von `PROJECT.md`.

## Arbeitsweise
- Kommunikation auf **Deutsch**.
- Code wird hier auf dem Windows-PC geschrieben, per **scp/ssh auf den Pi** kopiert und **dort ausgeführt**. Erkennung und Steuerung laufen auf dem Pi, nicht auf dem PC.
- Zugangsdaten zum Pi (`PI_HOST`, `PI_USER`, `PI_PASSWORD`) liegen in `.env` (Vorlage: `.env.example`). `.env` ist in `.gitignore` und wird **nie committet oder ausgegeben**. Skripte lesen die Werte selbst ein (z. B. Python mit `paramiko`), das Passwort wird nicht im Chat oder in Kommandozeilen angezeigt.
- Langfristig ist SSH-Key-Login besser als Passwort-Login.
- Den Freenove-Originalcode auf dem Pi **nicht verändern**. Er wird nur importiert bzw. als Referenz genutzt. Eigener Code liegt in einem eigenen Ordner auf dem Pi.
- Debug-Ausgaben (z. B. Kamerabilder mit Erkennungs-Overlay) auf dem Pi speichern und zum Ansehen auf den PC holen.

## Sicherheit beim Testen
- Vor jedem Motor-Test fragen, ob das Auto aufgebockt ist oder auf dem Boden steht.
- Motorbefehle immer **zeitlich begrenzen** und im `finally` die Motoren stoppen, auch bei Exceptions und Ctrl+C.

## PROJECT.md aktuell halten
- Sobald ein offener Punkt geklärt ist (Hostname, User, Pfade, PCB-Version, Umgebung), in `PROJECT.md` eintragen und abhaken.
- Fortschritt beim Vorgehen dort ebenfalls festhalten, damit die nächste Session nahtlos weitermachen kann.
