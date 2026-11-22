# Glossar

Die wichtigsten Begriffe, alphabetisch. Der Verweis zeigt, wo der Begriff ausführlich erklärt wird.

| Begriff | Bedeutung | Mehr dazu |
|---|---|---|
| **ADC** | Analog-Digital-Wandler. Hier der ADS7830, der die Akkuspannung misst. Einzelmessungen springen, deshalb den Median mehrerer Messungen nehmen. | [Übung 3](../exercises/drive_exercise_1.md) |
| **Anfahrverzug** | Zeit, bis die Motoren nach dem Einschalten wirklich Strecke machen, hier etwa 0,12 s. Kurze Impulse fahren deshalb deutlich weniger als Geschwindigkeit × Zeit. | [Übung 6](../exercises/park_exercise_1.md) |
| **Ausreißer** | Messwerte, die weit von den übrigen abweichen, z. B. falsch zugeordnete Bildpunkte. Werden vor der Mittelung verworfen. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Bewegungsunschärfe** | Verschmiertes Bild, weil sich Auto oder Kamera während der Belichtung bewegen. Bei Kunstlicht (lange Belichtung) besonders stark. | [Übung 5](../exercises/align_exercise_1.md) |
| **Bildwinkel (HFOV)** | Horizontaler Öffnungswinkel der Kamera, laut Datenblatt 53,5°. Daraus folgt die Brennweite in Pixeln. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Bodenmodell** | Formel, die einer Bildzeile einen Abstand auf dem Boden zuordnet, aus Kamerahöhe, Neigung und Brennweite. | [Übung 5b](../exercises/calibration_exercise_1.md) |
| **Brennweite (in Pixeln)** | Rechengröße des Lochkamera-Modells, hier f ≈ 634 px bei 640 × 480. Verbindet Pixelabstände mit Winkeln. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Drift** | Aufsummierte kleine Messfehler, die mit jedem Schritt größer werden. Typisch für jede Form von Odometrie. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Fit (kleinste Quadrate)** | Modellparameter so wählen, dass die Summe der quadrierten Abweichungen zu den Messpunkten minimal wird. | [Übung 5b](../exercises/calibration_exercise_1.md) |
| **Gyroskop / IMU** | Sensor, der Drehraten misst. Fehlt beim Freenove-Auto, deshalb wird der Drehwinkel mit der Kamera bestimmt. | [Übung 4](../exercises/turn_exercise_1.md) |
| **HSV** | Farbraum aus Farbton (Hue), Sättigung (Saturation) und Helligkeit (Value). Für Farberkennung robuster als RGB, weil der Farbton kaum vom Licht abhängt. In OpenCV läuft H von 0 bis 179. | [Übung 2](../exercises/cv_exercise_1.md) |
| **Kalibrieren** | Programmkonstanten aus Messungen am echten Gerät bestimmen, statt sie zu schätzen oder aus Datenblättern zu übernehmen. | [Übung 5b](../exercises/calibration_exercise_1.md) |
| **Koppelnavigation (Dead Reckoning)** | Position aus bekannter Geschwindigkeit und Zeit fortschreiben, ohne Sicht auf das Ziel. Hier für die letzten Zentimeter beim Parken. | [Übung 6](../exercises/park_exercise_1.md) |
| **Kontur** | Umriss einer zusammenhängenden Fläche in einer Maske. Die größte grüne Kontur ist das Blatt. | [Übung 2](../exercises/cv_exercise_1.md) |
| **Korrelierte Parameter** | Zwei Modellparameter, die sich gegenseitig ausgleichen können (hier Kamerahöhe und Brennweite). Die Messpunkte passen dann für viele Kombinationen gleich gut. | [Übung 5b](../exercises/calibration_exercise_1.md) |
| **Lochkamera-Modell** | Einfachstes Kameramodell: Ein Punkt im Winkel α zur Bildmitte landet bei x = f · tan(α) Pixeln von der Bildmitte. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Maske** | Schwarz-Weiß-Bild, in dem jedes Pixel angibt, ob es eine Bedingung erfüllt (z. B. „ist grün“). | [Übung 2](../exercises/cv_exercise_1.md) |
| **Matching** | Zuordnen gleicher markanter Punkte in zwei Bildern. Aus der Verschiebung folgt die Bewegung der Kamera. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Median** | Mittlerer Wert einer sortierten Liste. Unempfindlich gegen einzelne Ausreißer, anders als der Mittelwert. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Moment / Schwerpunkt** | Kennzahlen einer Kontur. Aus den Momenten folgt der Flächenschwerpunkt, also die Position des Blattes im Bild. | [Übung 2](../exercises/cv_exercise_1.md) |
| **Morphologie (Öffnen, Schließen)** | Bildoperationen auf Masken. Öffnen entfernt kleine Störflecken, Schließen füllt Lücken, z. B. durch Reflexe. | [Übung 2](../exercises/cv_exercise_1.md) |
| **ORB** | Verfahren, um markante Punkte (Ecken, Kanten) in einem Bild zu finden und so zu beschreiben, dass sie im nächsten Bild wiedererkannt werden. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Pan / Tilt** | Schwenken links/rechts bzw. Neigen hoch/runter des Kamerakopfs. Pan = Servo-Kanal `"1"`, Tilt = Kanal `"0"`. | [Übung 1](../exercises/head_movement_exercise_1.md) |
| **PCA9685** | PWM-Baustein am I2C-Bus, der Motoren und Servos ansteuert. Behält den letzten Befehl, auch wenn das Skript abstürzt. | [Übung 3](../exercises/drive_exercise_1.md) |
| **picamera2** | Python-Bibliothek für die Pi-Kamera. Auf Bookworm statt `cv2.VideoCapture` zu verwenden. | [Übung 1](../exercises/head_movement_exercise_1.md) |
| **PWM** | Pulsweitenmodulation. Die Motorleistung wird über das Verhältnis von An- zu Aus-Zeit eingestellt, hier mit Werten von −4095 bis 4095. | [Übung 3](../exercises/drive_exercise_1.md) |
| **Regelkreis** | Messen, mit dem Ziel vergleichen, korrigieren, erneut messen. Genauer als eine einmalige Vorab-Berechnung, weil Fehler laufend ausgeglichen werden. | [Übung 4](../exercises/turn_exercise_1.md), [Übung 5](../exercises/align_exercise_1.md) |
| **Servo** | Motor, der einen vorgegebenen Winkel anfährt und hält, statt sich frei zu drehen. | [Übung 1](../exercises/head_movement_exercise_1.md) |
| **Skid-Steering (Panzerlenkung)** | Lenken ohne lenkbare Räder: Die Räder einer Seite laufen schneller oder rückwärts. Die Reifen rutschen dabei, die Drehrate schwankt. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Tailscale** | Privates, verschlüsseltes Netz zwischen Geräten. Damit ist der Pi ohne Portfreigabe von überall erreichbar. | [Zugang und Setup](../KOLLEGEN_ANLEITUNG.md) |
| **Toter Winkel** | Bereich direkt vor dem Auto, den die Kamera nicht sieht, hier 3,7 cm ab der Vorderkante bei Tilt 110. | [Übung 5b](../exercises/calibration_exercise_1.md), [Übung 6](../exercises/park_exercise_1.md) |
| **Visual Servoing** | Regelung direkt auf Bildmerkmale: Das Auto dreht, bis das Ziel in der Bildmitte liegt. Das Ziel selbst ist der Sensor. | [Übung 5](../exercises/align_exercise_1.md) |
| **Visuelle Odometrie** | Eigenbewegung aus aufeinanderfolgenden Kamerabildern bestimmen. Hier: Drehwinkel aus der Verschiebung markanter Punkte. | [Übung 4](../exercises/turn_exercise_1.md) |
| **Zustandsautomat** | Programm, das sich immer in genau einem Zustand befindet (z. B. SUCHEN, AUSRICHTEN, ANFAHREN, PARKEN) und bei bestimmten Ereignissen wechselt. | [Übung 5](../exercises/align_exercise_1.md), [Übung 7](../exercises/mission_exercise_1.md) |
