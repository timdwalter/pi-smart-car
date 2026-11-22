# Kapitel 1: Sehen

Bevor sich ein Rad dreht, muss das Auto **sehen** können. Die Kamera ist der wichtigste Sensor des Projekts: Sie erkennt das Ziel, misst später Drehwinkel und schätzt Abstände.

Die beiden Übungen dieses Kapitels bewegen nur den Kamerakopf, nicht die Räder. Sie sind deshalb gefahrlos und eignen sich gut als Einstieg, auch remote.

- **Übung 1** klärt, wohin die Kamera bei welchem Servo-Wert schaut. Schon hier zeigt sich ein Grundsatz des ganzen Projekts: messen statt der Dokumentation glauben. Die Belegung der Servos war anders als in den Freenove-Kommentaren.
- **Übung 2** macht aus einem Foto **Zahlen**: Wo liegt das grüne Blatt im Bild, wie groß ist es, wie weit ist es ungefähr weg? Diese Zahlen (`offset_x`, `pos_y`, `area_fraction`) sind die Grundlage aller späteren Entscheidungen.
