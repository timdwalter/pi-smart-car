"""Zentrale Kalibrierwerte des Autos. Alle Übungen importieren von hier.

Werte, die am echten Auto gemessen wurden, stehen hier EINMAL, statt in jedem Skript.
"""

# Kamera-Servos (siehe Übung 1): Kanal "0" = Tilt, Kanal "1" = Pan
SERVO_TILT = "0"
SERVO_PAN = "1"

# Pan-Wert, bei dem die Kamera wirklich GERADEAUS schaut.
# Der Kamerakopf ist mechanisch verdreht: Bei Pan 90 schaut er ca. 18° nach LINKS.
# Richtung (gemessen 2026-11-22): GRÖSSERE Pan-Werte schauen nach LINKS, ca. 0,85° pro Einheit (kalibriert)
# (erste grobe Messung: Pan 90 -> 100 ließ das Blatt von +2,8° auf +13,6° wandern)
# Kalibriert 2026-11-22 mit calibrate_pan.py (Blatt exakt vor dem Auto): Nulldurchgang zwischen
# Pan 65 (-0,7°) und 70 (+3,2°) -> 66. Linearer Bereich 65-85: ca. 0,85° pro Einheit.
PAN_CENTER = 66

TILT_SEARCH = 90   # Suchen: Horizont im oberen Viertel
TILT_NEAR = 110    # Nahbereich: nur Boden vor dem Auto

# Kameralinse sitzt (bei Tilt 110) ca. 1,5-2 cm HINTER der Vorderkante des Autos (gemessen 2026-11-22).
# Abstände, die ab der Vorderkante gemessen werden, + diesen Wert = Abstand ab Linse.
LENS_BEHIND_FRONT_CM = 1.75

# Boden-Kalibrierung bei Tilt 110 (2026-11-22, ground_calibration.py, Blatt bei 5/10/20 cm ab Autokante).
# Mit Lineal grob gemessen: Linse "etwa 7 cm" hoch. Die Messpunkte lassen Höhe und Brennweite aber nicht
# sauber trennen. Mit der in Übung 4 bestätigten Brennweite (634 px) ergibt der Fit:
CAMERA_HEIGHT_CM = 5.2        # Linsenmitte über dem Boden (Fit, RMS 0,05 cm)
TILT_NEAR_PITCH_DEG = 23.0    # Neigung der Kamera unter die Waagerechte bei TILT_NEAR (110)
DEAD_ZONE_FROM_LENS_CM = 5.4  # toter Winkel: unterer Bildrand liegt 5,4 cm vor der Linse (= 3,7 cm ab Autokante)
