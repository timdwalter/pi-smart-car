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
