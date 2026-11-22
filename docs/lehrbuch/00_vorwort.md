# Vorwort

## Worum es geht

Ein Bausatz-Auto aus dem Hobbyregal, ein Raspberry Pi 4 und eine Kamera, die kaum höher als eine Kaffeetasse über dem Boden sitzt. Damit soll eine Aufgabe gelöst werden, die einfach klingt:

> Das Auto erkennt ein **grünes Blatt Papier** auf dem Boden, dreht sich dorthin, fährt hin und **parkt mittig darauf**, vollständig autonom.

Das ist **Stufe 1** des Projekts, und sie ist erreicht: Aus etwa 1,5 m Entfernung und beliebiger Ausrichtung findet das Auto das Blatt in rund 25 Sekunden und bleibt mit allen Rädern darauf stehen.

Der Weg dorthin ist der eigentliche Inhalt dieses Buches. Das Auto hat kein Gyroskop und keine Radencoder, der Kamerakopf ist verdreht und wackelt, der Laminatboden spiegelt, und bei Kunstlicht verschmiert jedes Bild. Fast jedes Problem, das in echter Robotik auftritt, taucht hier im Kleinen auf. Die Lösungen sind deshalb keine Theorie, sondern am echten Auto gemessen und mehrfach korrigiert.

## Für wen das Buch ist

Für Kolleginnen und Kollegen aus der **IoT-Hacking-Community**, die am SmartCar mitarbeiten oder sich Wissen zu Bildverarbeitung und mobiler Robotik aneignen wollen.

Vorausgesetzt werden:

- **Python-Grundkenntnisse** (Funktionen, Schleifen, Bibliotheken importieren)
- Umgang mit einem **Terminal** (PowerShell, Git Bash oder Linux-Shell)
- Neugier. Mathematik kommt vor (Winkel, ein wenig Trigonometrie, ein Fit nach kleinsten Quadraten), wird aber Schritt für Schritt hergeleitet.

Vorwissen zu Robotik oder OpenCV ist **nicht** nötig.

## Aufbau

| Teil | Inhalt |
|---|---|
| **I – Einstieg** | Zugang zum Auto per Tailscale, Projekt einrichten, Spielregeln, das Auto im Überblick |
| **II – Übungen** | Acht aufeinander aufbauende Übungen, vom ersten Kamerabild bis zur kompletten Mission |
| **III – Weiter geht's** | Offene Baustellen als Projektaufgaben zum Mitmachen |
| **Anhang** | Betriebshandbuch (Belegungen, Befehle, Messwerte, Fehlerbehebung) und Glossar |

Jede Übung besteht aus zwei Teilen:

- **Teil A – Lecture:** das Problem, die Theorie Schritt für Schritt, Code-Ausschnitte und Ergebnisse echter Testläufe, einschließlich der Fehlschläge. Dieser Teil eignet sich zum Selbstlesen und zum Vortragen.
- **Teil B – Exercise:** Sicherheitshinweise, Befehle zum Ausprobieren, Aufgaben und Lösungen zum Aufklappen. Dieser Teil wird am Auto gemacht.

## Der Lernpfad

```
Kapitel 1  Sehen              1 Kamerakopf ──▶ 2 Grün erkennen ──┐
Kapitel 2  Bewegen            3 Fahren ──────────────────────────┴──▶ 4 Drehen ohne Gyro
Kapitel 3  Finden und messen  5 Ausrichten ──▶ 5b Kalibrieren
Kapitel 4  Ankommen           6 Parken ──▶ 7 Mission (Stufe 1 ✓)
```

Die Übungen sind in dieser Reihenfolge am sinnvollsten, weil jede auf Bausteinen der vorherigen aufbaut. Wer nur einzelne Themen sucht, findet im Glossar zu jedem Begriff die Übung, in der er erklärt wird.

| Übung | Thema | Dauer (ca.) |
|---|---|---|
| 1 | Kamerakopf bewegen | 20–30 min |
| 2 | Grünes Blatt erkennen | 45–60 min |
| 3 | Vorwärts und rückwärts fahren | 20–30 min |
| 4 | Um 90° drehen, ohne Gyroskop | 60–90 min |
| 5 | Blatt suchen und ausrichten | 45–60 min |
| 5b | Kamera und Fahrzeug kalibrieren | 60–90 min |
| 6 | Hinfahren und parken | 60–90 min |
| 7 | Die ganze Mission | 45–60 min |

Insgesamt sind es etwa **sieben Stunden**, gut verteilt auf mehrere IoT-Hacking-Abende.

## Wie dieses Buch entsteht

Das Buch wird aus der Dokumentation im Repository **gebaut**. Die Übungen in `docs/exercises/`, das Betriebshandbuch und die Einstiegsanleitung sind die eigentliche Quelle. Das Skript `tools/build_lehrbuch.py` setzt sie mit den Rahmentexten aus `docs/lehrbuch/` zu dieser einen Datei zusammen. Wer eine Übung verbessert, verbessert damit automatisch das Buch.

Entwickelt wurde das Projekt überwiegend im Dialog mit **Claude Code**. Die Regeln dafür (Sicherheit bei Motortests, Doku-Konventionen, zentrale Kalibrierwerte) stehen in `CLAUDE.md` im Repository und gelten für Menschen genauso.
