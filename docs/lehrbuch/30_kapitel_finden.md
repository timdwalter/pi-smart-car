# Kapitel 3: Finden und messen

Mit Sehen und Bewegen lassen sich die ersten Bausteine kombinieren: Das Auto soll das Blatt **suchen** und sich genau darauf **ausrichten**.

- **Übung 5** baut dafür einen ersten **Zustandsautomaten** (SUCHEN, AUSRICHTEN) und nutzt das Blatt im Bild direkt als Sensor (Visual Servoing). Die Übung dokumentiert ausführlich, was in einer echten Wohnung alles schiefging: Reflexe, Bewegungsunschärfe, Pendeln um das Ziel und ein Kamerakopf, der schief schaut.
- **Übung 5b** zieht daraus die Konsequenz: Ohne **gemessene** Werte funktioniert nichts zuverlässig. Pan-Nullpunkt, Geschwindigkeit, toter Winkel und ein Bodenmodell (Bildzeile → Abstand in cm) werden kalibriert, einschließlich der Irrwege beim Fitten.
