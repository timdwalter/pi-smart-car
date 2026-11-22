# Kapitel 2: Bewegen

Jetzt bewegt sich das Auto wirklich. Damit gelten ab hier die **Spielregeln** aus Teil I: vorher klären, ob das Auto aufgebockt ist oder auf dem Boden steht, jeden Motorbefehl zeitlich begrenzen und im `finally` stoppen.

- **Übung 3** steuert die Motoren an, prüft vorab Akku und Ultraschall und zeigt, wie stark die Spannung beim Anfahren einbricht.
- **Übung 4** ist das Herzstück des Kapitels: Das Auto soll sich um genau 90° drehen, obwohl es weder Gyroskop noch Radencoder hat. Die Lösung kommt aus Kapitel 1. Die Kamera vergleicht Fotos vor und nach jedem kurzen Drehimpuls und berechnet aus der Verschiebung markanter Punkte den Winkel (visuelle Odometrie).
