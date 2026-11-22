"""Wie weit fährt ein KURZER Fahrimpuls wirklich?

Die Geschwindigkeit 50 cm/s wurde mit 1 s Fahrt gemessen. Kurze Impulse bestehen aber
fast nur aus Anfahren und kommen nicht so weit. Dieses Skript misst das mit der Kamera:

Das Auto steht VOR oder AUF dem grünen Blatt, die HINTERE Blattkante ist bei Tilt 110 im Bild.
Über das Bodenmodell (Übung 5b) wird ihr Abstand zur Linse berechnet. Dann wird ein kurzer
Vorwärtsimpuls gefahren und neu gemessen. Differenz = tatsächlich gefahrene Strecke.

Aufruf auf dem Pi:
  python3 pulse_calibration.py [dauer_s=0.16] [anzahl=3] [speed=1500]
Stoppt vorher, wenn die Kante näher als STOP_CM kommt oder verschwindet.
"""
import math
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from Motor import Motor  # noqa: E402
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_exercise_1 import detect_green, draw  # noqa: E402
from turn_exercise_1 import FOCAL_PX, W, H  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
STOP_CM = 7.0  # Kante darf nicht in den toten Winkel (5,4 cm ab Linse) laufen


def ground_dist(y: float) -> float:
    """Bodenabstand ab Linse für Bildzeile y (Modell aus ground_calibration.py, Tilt 110)."""
    ang = math.radians(cfg.TILT_NEAR_PITCH_DEG) + math.atan((y - H / 2) / FOCAL_PX)
    return cfg.CAMERA_HEIGHT_CM / math.tan(ang) if ang > 0 else float("inf")


def far_edge(frame):
    """Oberste grüne Zeile in der Bildmitte = hintere Blattkante. None, wenn nicht sichtbar."""
    mask, res = detect_green(frame)
    col = mask[:, W // 2 - 5: W // 2 + 5]
    rows = [r for r in range(H) if col[r].any()]
    if not rows or min(rows) <= 2:  # Kante oben abgeschnitten -> nicht messbar
        return None, draw(frame, res)
    y = min(rows)
    out = draw(frame, res)
    cv2.line(out, (0, y), (W, y), (255, 0, 255), 1)
    return y, out


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 0.16
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    speed = int(sys.argv[3]) if len(sys.argv) > 3 else 1500

    servo = Servo()
    servo.setServoPwm(cfg.SERVO_TILT, cfg.TILT_NEAR)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
    motor = Motor()
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)

    def measure(tag):
        time.sleep(0.4)  # Nachrollen / Wackeln abklingen lassen (Bewegungsunschärfe!)
        y, out = far_edge(cam.capture_array())
        cv2.imwrite(str(DEBUG / f"pulse_{tag}.jpg"), out)
        return y, (ground_dist(y) if y is not None else None)

    try:
        y, d = measure("0")
        if d is None:
            print("Hintere Blattkante nicht sichtbar - Auto vor/auf das Blatt stellen.")
            return
        print(f"Start: Kante bei y={y} -> {d:.1f} cm ab Linse")
        moved = []
        for i in range(1, n + 1):
            if d < STOP_CM:
                print(f"Kante nur noch {d:.1f} cm entfernt - Stopp (toter Winkel bei 5,4 cm).")
                break
            motor.setMotorModel(speed, speed, speed, speed)
            time.sleep(dur)
            motor.setMotorModel(0, 0, 0, 0)
            y2, d2 = measure(str(i))
            if d2 is None:
                print(f"Impuls {i}: Kante nicht mehr messbar - Stopp.")
                break
            moved.append(d - d2)
            print(f"Impuls {i} ({dur:.2f} s @ {speed}): Kante y={y2} -> {d2:.1f} cm, gefahren {d - d2:.1f} cm")
            y, d = y2, d2
        if moved:
            avg = sum(moved) / len(moved)
            print(f"=> Mittel {avg:.1f} cm pro {dur:.2f}-s-Impuls "
                  f"(effektiv {avg / dur:.0f} cm/s statt {50 * dur:.1f} cm bei 50 cm/s)")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
