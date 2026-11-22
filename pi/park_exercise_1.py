"""Übung 6: Zum grünen Blatt fahren und mittig darauf parken.

Zustandsautomat (schrittweise, Stop-and-Go):
  AUSRICHTEN  -> Blatt suchen und mittig ausrichten (Übung 5)
  ANFAHREN    -> kurze Vorwärtsimpulse; nach jedem Impuls Blatt prüfen und Richtung korrigieren.
                 Kommt das Blatt unten im Bild an (pos_y groß), Kamera auf Nahbereich (Tilt 110) senken.
  EINPARKEN   -> Die vordere Blattkante verschwindet unten aus dem Bild. Ab jetzt ist das Blatt
                 im "toten Winkel" vor dem Auto. Die restliche Strecke wird blind gefahren:
                     rest = TOTER_WINKEL_CM + BLATT_LAENGE_CM / 2 - KAMERA_VOR_MITTE_CM
                 Dafür muss man die Geschwindigkeit in cm/s kennen (Kalibrierung).
  FERTIG

Aufruf auf dem Pi:
  python3 park_exercise_1.py kalibrieren   -> Kamera auf Tilt 110, Bild speichern (toter Winkel messen)
  python3 park_exercise_1.py [speed=1500]  -> Parken

Debug-Bilder in ~/smartcar/debug/: park_<schritt>.jpg
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
from picamera2 import Picamera2  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_exercise_1 import detect_green, draw  # noqa: E402
from align_exercise_1 import offset_to_angle  # noqa: E402
from turn_exercise_1 import W, H  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

# ---------------- KALIBRIERWERTE (noch zu messen!) ----------------
SPEED_CM_PER_S = None        # Fahrgeschwindigkeit bei DRIVE_SPEED, z. B. 25.0 (Übung 3, Aufgabe 2)
TOTER_WINKEL_CM = None       # Abstand Kamera -> unterer Bildrand auf dem Boden bei Tilt 110
KAMERA_VOR_MITTE_CM = None   # wie weit die Kamera vor der Mitte des Autos sitzt
BLATT_LAENGE_CM = 29.7       # DIN A4 längs; 21.0 wenn quer
# -------------------------------------------------------------------

DRIVE_SPEED = 1500
TURN_SPEED = 2000
TILT_FAR = cfg.TILT_SEARCH   # Suchen / Anfahren aus der Ferne
TILT_NEAR = cfg.TILT_NEAR    # Nahbereich
POS_Y_SWITCH = 0.75          # ab hier Kamera senken
BOTTOM_MARGIN_PX = 5         # Blatt-Unterkante "berührt" den Bildrand
DRIVE_PULSE_S = 0.4
ALIGN_TOLERANCE_DEG = 5.0    # beim Anfahren etwas großzügiger als in Übung 5
MIN_VOLTAGE = 6.5
MIN_FRONT_CM = 15            # Ultraschall: Hindernis -> Not-Stopp
MAX_STEPS = 60


def calibrated() -> bool:
    return None not in (SPEED_CM_PER_S, TOTER_WINKEL_CM, KAMERA_VOR_MITTE_CM)


def kalibrieren():
    servo = Servo()
    servo.setServoPwm(cfg.SERVO_TILT, TILT_NEAR)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
    cam = Picamera2()
    cam.configure(cam.create_still_configuration(main={"size": (W, H)}))
    cam.start()
    time.sleep(1.5)
    path = DEBUG / "park_kalibrierung_tilt110.jpg"
    cam.capture_file(str(path))
    cam.stop()
    cam.close()
    print(f"Bild gespeichert: {path}")
    print("Jetzt messen:")
    print("  1. TOTER_WINKEL_CM: Ein Lineal/Maßband längs vor das Auto legen. Welcher Abstand")
    print("     (ab Kamera-Linse, auf dem Boden) ist gerade noch am unteren Bildrand sichtbar?")
    print("  2. KAMERA_VOR_MITTE_CM: Abstand Kamera-Linse -> Mitte zwischen den vier Rädern.")
    print("  3. SPEED_CM_PER_S: drive_exercise_1.py 1500 1 fahren und die Strecke messen.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "kalibrieren":
        kalibrieren()
        return
    if not calibrated():
        print("Noch nicht kalibriert! Bitte oben im Skript eintragen:")
        print(f"  SPEED_CM_PER_S={SPEED_CM_PER_S}, TOTER_WINKEL_CM={TOTER_WINKEL_CM}, "
              f"KAMERA_VOR_MITTE_CM={KAMERA_VOR_MITTE_CM}")
        print("Hilfe: python3 park_exercise_1.py kalibrieren")
        return

    drive_speed = int(sys.argv[1]) if len(sys.argv) > 1 else DRIVE_SPEED
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    motor, adc, servo = Motor(), Adc(), Servo()
    v = adc.recvADC(2) * 3
    print(f"Akku: {v:.2f} V")
    if v < MIN_VOLTAGE:
        print(f"ABBRUCH: Akku unter {MIN_VOLTAGE} V")
        return
    try:
        from Ultrasonic import Ultrasonic
        sonar = Ultrasonic()
    except Exception:
        sonar = None

    servo.setServoPwm(cfg.SERVO_TILT, TILT_FAR)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)  # wirklich geradeaus, nicht 90!
    tilt = TILT_FAR
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)

    def grab():
        time.sleep(0.4)
        return cam.capture_array()

    def pulse(fl_bl: int, fr_br: int, seconds: float):
        motor.setMotorModel(fl_bl, fl_bl, fr_br, fr_br)
        time.sleep(seconds)
        motor.setMotorModel(0, 0, 0, 0)

    state = "ANFAHREN"  # Voraussetzung: vorher align_exercise_1.py ausgeführt
    try:
        for step in range(1, MAX_STEPS + 1):
            frame = grab()
            _, res = detect_green(frame)
            cv2.imwrite(str(DEBUG / f"park_{step:02d}.jpg"), draw(frame, res))

            if sonar is not None:
                d = sonar.get_distance()
                if 0 < d < MIN_FRONT_CM:
                    print(f"NOT-STOPP: Hindernis {d} cm vor dem Auto")
                    break

            if res is None:
                print(f"Schritt {step}: Blatt nicht sichtbar (Tilt {tilt}). ABBRUCH, erst Übung 5 ausführen.")
                break

            x, y, bw, bh = res["bbox"]
            angle = offset_to_angle(res["offset_x"])
            print(f"Schritt {step} [{state}] Tilt {tilt}: Winkel {angle:+5.1f}°, pos_y {res['pos_y']:.2f}, "
                  f"Unterkante y={y + bh}")

            # Richtung korrigieren
            if abs(angle) > ALIGN_TOLERANCE_DEG:
                s = TURN_SPEED if angle < 0 else -TURN_SPEED  # Blatt links -> links drehen
                pulse(-s, s, min(0.3, 0.8 * abs(angle) / 55.0))
                continue

            # Kamera auf Nahbereich umschalten
            if tilt == TILT_FAR and res["pos_y"] > POS_Y_SWITCH:
                tilt = TILT_NEAR
                servo.setServoPwm(cfg.SERVO_TILT, tilt)
                time.sleep(0.5)
                print("  -> Kamera auf Nahbereich (Tilt 110)")
                continue

            # Vordere Blattkante erreicht den unteren Bildrand -> blind einparken
            if tilt == TILT_NEAR and y + bh >= H - BOTTOM_MARGIN_PX:
                rest_cm = TOTER_WINKEL_CM + BLATT_LAENGE_CM / 2 - KAMERA_VOR_MITTE_CM
                rest_s = rest_cm / SPEED_CM_PER_S
                print(f"EINPARKEN: noch {rest_cm:.1f} cm blind fahren ({rest_s:.2f} s)")
                pulse(drive_speed, drive_speed, rest_s)
                print("FERTIG: geparkt.")
                break

            pulse(drive_speed, drive_speed, DRIVE_PULSE_S)
        else:
            print(f"ABBRUCH: maximal {MAX_STEPS} Schritte erreicht.")
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
