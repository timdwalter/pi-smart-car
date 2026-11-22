"""Übung 6: Zum grünen Blatt fahren und mittig darauf parken.

Zustandsautomat (schrittweise, Stop-and-Go):
  AUSRICHTEN  -> Blatt suchen und mittig ausrichten (Übung 5)
  ANFAHREN    -> kurze Vorwärtsimpulse; nach jedem Impuls Blatt prüfen und Richtung korrigieren.
                 Kommt das Blatt unten im Bild an (pos_y groß), Kamera auf Nahbereich (Tilt 110) senken.
  EINPARKEN   -> Die vordere Blattkante verschwindet unten aus dem Bild. Ab jetzt ist das Blatt
                 im "toten Winkel" vor dem Auto. Die restliche Strecke wird blind gefahren.
                 Bezugspunkt ist die HINTERE Blattkante, die noch sichtbar ist. Ihr Abstand zur Linse
                 kommt aus dem Bodenmodell (Übung 5b):
                     rest = d_hinterkante - BLATT_LAENGE_CM / 2 + KAMERA_VOR_MITTE_CM
                 Ist die Hinterkante nicht messbar, gilt die Formel über den toten Winkel:
                     rest = TOTER_WINKEL_CM + BLATT_LAENGE_CM / 2 + KAMERA_VOR_MITTE_CM
                 (Erster Testlauf hatte hier "- KAMERA_VOR_MITTE_CM": Vorzeichenfehler, ~8 cm zu kurz.)
                 Dafür muss man die Geschwindigkeit in cm/s kennen (Kalibrierung).
  FERTIG

Aufruf auf dem Pi:
  python3 park_exercise_1.py kalibrieren   -> Kamera auf Tilt 110, Bild speichern (toter Winkel messen)
  python3 park_exercise_1.py [speed=1500]  -> Parken

Debug-Bilder in ~/smartcar/debug/: park_<schritt>.jpg
"""
import math
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
from align_exercise_1 import offset_to_angle, looks_like_sheet, open_camera  # noqa: E402
from turn_exercise_1 import W, H, FOCAL_PX  # noqa: E402
from ground_calibration import model as ground_model  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

# ---------------- KALIBRIERWERTE (noch zu messen!) ----------------
SPEED_CM_PER_S = 50.0        # gemessen 2026-11-22: Speed 1500, 1,0 s -> ~50 cm (inkl. Anfahren)
ANFAHR_VERZUG_S = 0.12       # Zeit, die beim Anfahren "verloren" geht. Aus zwei Parkläufen:
                             # 0,16 s -> ~2 cm statt 8, 0,43 s -> ~15,6 cm statt 21,6 (je ~6-8 cm zu kurz)
TOTER_WINKEL_CM = cfg.DEAD_ZONE_FROM_LENS_CM  # Linse -> unterer Bildrand bei Tilt 110 (kalibriert: 5,4 cm)
KAMERA_VOR_MITTE_CM = 7.75   # Auto 19 cm lang -> Mitte 9,5 cm hinter der Vorderkante, Linse 1,75 cm dahinter
BLATT_LAENGE_CM = 21.0       # DIN A4 QUER zur Fahrtrichtung (im Bild nachgemessen: ~19 cm); 29.7 wenn längs
# -------------------------------------------------------------------

DRIVE_SPEED = 1500
TURN_SPEED = 2000
TILT_FAR = cfg.TILT_SEARCH   # Suchen / Anfahren aus der Ferne
TILT_NEAR = cfg.TILT_NEAR    # Nahbereich
POS_Y_SWITCH = 0.6           # ab hier Kamera senken (erster Test: 0.75 kam einen Impuls zu spät)
BOTTOM_MARGIN_PX = 5         # Blatt-Unterkante "berührt" den Bildrand
DRIVE_PULSE_S = 0.4          # fern
NEAR_PULSE_S = 0.2           # Nahbereich: kleinere Schritte (~8-10 cm)
SETTLE_S = 0.8               # nach jedem Impuls warten, bis das Auto ruhig steht
RETRIES = 2                  # Blatt nicht erkannt -> so oft neu fotografieren, bevor abgebrochen wird
ALIGN_TOLERANCE_DEG = 5.0    # beim Anfahren etwas großzügiger als in Übung 5
MIN_VOLTAGE = 6.5
MIN_FRONT_CM = 15            # Ultraschall: Hindernis -> Not-Stopp
MAX_STEPS = 60


def far_edge_cm(mask, bbox):
    """Abstand der HINTEREN Blattkante zur Linse (Bodenmodell, Tilt 110), gemessen in der Bildmitte.

    None, wenn die Kante oben abgeschnitten oder in der Bildmitte kein Blatt ist."""
    x, y, bw, bh = bbox
    col = mask[y:y + bh, W // 2 - 5: W // 2 + 5]
    rows = [r for r in range(bh) if col[r].any()]
    if not rows or y + rows[0] <= 2:
        return None
    return ground_model(y + rows[0], cfg.CAMERA_HEIGHT_CM, math.radians(cfg.TILT_NEAR_PITCH_DEG), FOCAL_PX)


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


def park(cam, motor, servo, sonar, drive_speed: int = DRIVE_SPEED, prefix: str = "park") -> bool:
    """Auf das (bereits ausgerichtete) Blatt zufahren und mittig darauf parken. True, wenn geparkt.

    Wird auch von mission_exercise_1.py genutzt."""
    servo.setServoPwm(cfg.SERVO_TILT, TILT_FAR)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)  # wirklich geradeaus, nicht 90!
    tilt = TILT_FAR

    def grab():
        # Nachwippen abwarten: Bei Kunstlicht belichtet die Kamera ~33 ms, jede Restbewegung
        # verschmiert das Blatt (erster 150-cm-Lauf: 0,4 s reichten nicht).
        time.sleep(SETTLE_S)
        cam.capture_array()            # ein Bild verwerfen (kann noch aus der Bewegung stammen)
        return cam.capture_array()

    def find(frame):
        if tilt == TILT_FAR:
            # wie Übung 5: nur flach UND unterhalb des Horizonts (Lichtreflexe oben im Bild ignorieren)
            return detect_green(frame, accept=looks_like_sheet)
        # Aus der Nähe füllt das Blatt das Bild, ist also nicht mehr "flach" -> ohne Formfilter
        return detect_green(frame)

    def pulse(fl_bl: int, fr_br: int, seconds: float):
        motor.setMotorModel(fl_bl, fl_bl, fr_br, fr_br)
        time.sleep(seconds)
        motor.setMotorModel(0, 0, 0, 0)

    for step in range(1, MAX_STEPS + 1):
        frame = grab()
        mask, res = find(frame)
        for retry in range(RETRIES):
            if res is not None:
                break
            print(f"Schritt {step}: Blatt nicht erkannt -> neues Foto ({retry + 1}/{RETRIES})")
            frame = grab()
            mask, res = find(frame)
        cv2.imwrite(str(DEBUG / f"{prefix}_{step:02d}.jpg"), draw(frame, res))

        if sonar is not None:
            d = sonar.get_distance()
            if 0 < d < MIN_FRONT_CM:
                print(f"NOT-STOPP: Hindernis {d} cm vor dem Auto")
                return False

        if res is None:
            print(f"Schritt {step}: Blatt nicht sichtbar (Tilt {tilt}). ABBRUCH, erst ausrichten (Übung 5).")
            return False

        x, y, bw, bh = res["bbox"]
        angle = offset_to_angle(res["offset_x"])
        print(f"Schritt {step} [ANFAHREN] Tilt {tilt}: Winkel {angle:+5.1f}°, pos_y {res['pos_y']:.2f}, "
              f"Unterkante y={y + bh}")

        # Richtung korrigieren
        if abs(angle) > ALIGN_TOLERANCE_DEG:
            s = TURN_SPEED if angle < 0 else -TURN_SPEED  # Blatt links -> links drehen
            pulse(-s, s, min(0.3, 0.8 * abs(angle) / 55.0))
            continue

        touches_bottom = y + bh >= H - BOTTOM_MARGIN_PX

        # Kamera auf Nahbereich umschalten (spätestens, wenn das Blatt unten anstößt)
        if tilt == TILT_FAR and (res["pos_y"] > POS_Y_SWITCH or touches_bottom):
            tilt = TILT_NEAR
            servo.setServoPwm(cfg.SERVO_TILT, tilt)
            time.sleep(0.5)
            print("  -> Kamera auf Nahbereich (Tilt 110)")
            continue

        # Vordere Blattkante erreicht den unteren Bildrand -> blind einparken
        if tilt == TILT_NEAR and touches_bottom:
            d_far = far_edge_cm(mask, res["bbox"])
            if d_far is not None:
                rest_cm = d_far - BLATT_LAENGE_CM / 2 + KAMERA_VOR_MITTE_CM
                how = f"Hinterkante {d_far:.1f} cm vor der Linse"
            else:
                rest_cm = TOTER_WINKEL_CM + BLATT_LAENGE_CM / 2 + KAMERA_VOR_MITTE_CM
                how = "Hinterkante nicht messbar, Formel über toten Winkel"
            rest_cm = max(0.0, rest_cm)
            rest_s = rest_cm / SPEED_CM_PER_S + ANFAHR_VERZUG_S if rest_cm > 0 else 0.0
            print(f"EINPARKEN ({how}): noch {rest_cm:.1f} cm blind fahren "
                  f"({rest_s:.2f} s inkl. {ANFAHR_VERZUG_S:.2f} s Anfahrverzug)")
            if rest_s > 0:
                pulse(drive_speed, drive_speed, rest_s)
            print("FERTIG: geparkt.")
            return True

        pulse(drive_speed, drive_speed, NEAR_PULSE_S if tilt == TILT_NEAR else DRIVE_PULSE_S)
    print(f"ABBRUCH: maximal {MAX_STEPS} Schritte erreicht.")
    return False


def open_sonar():
    try:
        from Ultrasonic import Ultrasonic
        return Ultrasonic()
    except Exception:
        return None


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

    cam = open_camera()
    try:
        park(cam, motor, servo, open_sonar(), drive_speed)
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
