"""Übung 7: Die ganze Mission in einem Programm - umschauen, suchen, ausrichten, hinfahren, parken.

Bausteine aus den vorherigen Übungen:
  - Grün-Erkennung            (Übung 2, cv_exercise_1)
  - Drehen + Odometrie        (Übung 4, turn_exercise_1)
  - Suchen + Ausrichten       (Übung 5, align_exercise_1.align)
  - Anfahren + Parken         (Übung 6, park_exercise_1.park)

Neu ist Phase 0 UMSCHAUEN: Bevor sich das Auto dreht, schwenkt nur der Kamerakopf nach links und
rechts. Liegt das Blatt irgendwo im Blickfeld, weiß das Auto, in welche Richtung es drehen muss.
(Ohne diesen Schritt hat sich das Auto im Test einmal fast komplett im Kreis gedreht, weil es
stur nach rechts gesucht hat, das Blatt aber links lag.)

Aufruf auf dem Pi:
  python3 mission_exercise_1.py [dreh_speed=2000] [fahr_speed=1500]
  python3 mission_exercise_1.py 0      -> Trockenlauf: nur umschauen, Motoren bleiben aus

Debug-Bilder in ~/smartcar/debug/: mission_scan_<grad>.jpg, mission_align_<n>.jpg, mission_park_<n>.jpg
"""
import signal
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from Motor import Motor  # noqa: E402
from ADC import Adc  # noqa: E402
from servo import Servo  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_exercise_1 import detect_green, draw  # noqa: E402
from align_exercise_1 import align, looks_like_sheet, offset_to_angle, open_camera  # noqa: E402
from park_exercise_1 import park, open_sonar  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

MIN_VOLTAGE = 6.8
PAN_DEG_PER_UNIT = 0.85          # kalibriert (calibrate_pan.py), größerer Pan-Wert = links
SCAN_DEG = [0, -25, 25, -45, 45]  # Blickrichtungen relativ zur Fahrtrichtung (+ = rechts)
                                  # Bildwinkel ±27° -> zusammen ca. ±72° abgedeckt


def pan_for(deg: float) -> int:
    """Blickwinkel (+ = rechts) -> Pan-Wert. Rechts = kleinere Pan-Werte."""
    return round(cfg.PAN_CENTER - deg / PAN_DEG_PER_UNIT)


def look_around(cam, servo):
    """Nur den Kopf schwenken. Liefert den Winkel zum Blatt relativ zur Fahrtrichtung oder None."""
    servo.setServoPwm(cfg.SERVO_TILT, cfg.TILT_SEARCH)
    best = None
    for deg in SCAN_DEG:
        servo.setServoPwm(cfg.SERVO_PAN, pan_for(deg))
        time.sleep(0.6)
        cam.capture_array()  # Bild aus der Schwenkbewegung verwerfen
        frame = cam.capture_array()
        _, res = detect_green(frame, accept=looks_like_sheet)
        cv2.imwrite(str(DEBUG / f"mission_scan_{deg:+d}.jpg"), draw(frame, res))
        if res is None:
            print(f"  Kopf {deg:+3d}°: nichts")
            continue
        total = deg + offset_to_angle(res["offset_x"])
        print(f"  Kopf {deg:+3d}°: Blatt bei {total:+5.1f}° (Fläche {res['area_fraction']*100:.1f} %)")
        if best is None or res["area_fraction"] > best[1]:
            best = (total, res["area_fraction"])
        if deg == 0:
            break  # schon geradeaus zu sehen -> nicht weiter schwenken
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
    time.sleep(0.5)
    return best[0] if best else None


def main():
    turn_speed = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    drive_speed = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    dry_run = turn_speed == 0

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    motor, adc, servo = Motor(), Adc(), Servo()
    # Median aus 5 Messungen: Einzelwerte springen (einmal 6,60 V gemessen, direkt danach 6,99-7,14 V)
    readings = []
    for _ in range(5):
        readings.append(adc.recvADC(2) * 3)
        time.sleep(0.1)
    v = sorted(readings)[2]
    print(f"Akku: {v:.2f} V")
    if v < MIN_VOLTAGE and not dry_run:
        print(f"ABBRUCH: Akku unter {MIN_VOLTAGE} V - erst laden (die Blindfahrt ist auf ~7-8 V kalibriert).")
        return

    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
    cam = open_camera()
    t0 = time.time()
    try:
        print("== Phase 0: UMSCHAUEN (nur Kamerakopf) ==")
        angle = look_around(cam, servo)
        if angle is None:
            direction = "rechts"
            print("Blatt nicht im Blickfeld (±72°) -> es liegt wohl hinter dem Auto, suche nach rechts.")
        else:
            direction = "rechts" if angle > 0 else "links"
            print(f"Blatt bei {angle:+.0f}° -> drehe nach {direction}.")
        if dry_run:
            print("Trockenlauf: Ende.")
            return

        print("== Phase 1+2: SUCHEN und AUSRICHTEN ==")
        if not align(cam, motor, direction, turn_speed, prefix="mission_align"):
            print("MISSION ABGEBROCHEN: nicht ausgerichtet.")
            return

        print("== Phase 3+4: ANFAHREN und PARKEN ==")
        ok = park(cam, motor, servo, open_sonar(), drive_speed, prefix="mission_park")
        print(f"MISSION {'ERFÜLLT' if ok else 'ABGEBROCHEN'} nach {time.time() - t0:.0f} s.")
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        servo.setServoPwm(cfg.SERVO_TILT, cfg.TILT_SEARCH)
        servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
