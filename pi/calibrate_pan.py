"""Kalibrierung: Bei welchem Pan-Wert schaut die Kamera wirklich geradeaus?

Vorbereitung: Das grüne Blatt EXAKT gerade vor das Auto legen (Mitte des Blattes auf der
Längsachse des Autos, ca. 50-100 cm entfernt).

Das Skript fährt den Pan-Servo durch mehrere Werte, erkennt jeweils das Blatt und berechnet,
wie weit es neben der Bildmitte liegt. Liegt das Blatt in der Bildmitte, schaut die Kamera
genau geradeaus. Per linearer Regression wird der Pan-Wert für "Winkel = 0" bestimmt.

Aufruf auf dem Pi:  python3 calibrate_pan.py [von=80] [bis=115] [schritt=5]
"""
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_exercise_1 import detect_green, draw  # noqa: E402
from turn_exercise_1 import FOCAL_PX, W, H  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 115
    st = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    servo = Servo()
    servo.setServoPwm(cfg.SERVO_TILT, cfg.TILT_SEARCH)
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)

    pans, angles = [], []
    try:
        for pan in range(lo, hi + 1, st):
            servo.setServoPwm(cfg.SERVO_PAN, pan)
            time.sleep(0.8)
            frame = cam.capture_array()
            _, res = detect_green(frame)
            cv2.imwrite(str(DEBUG / f"calpan_{pan}.jpg"), draw(frame, res))
            if res is None:
                print(f"Pan {pan:3d}: kein Blatt")
                continue
            angle = math.degrees(math.atan(res["offset_x"] * (W / 2) / FOCAL_PX))
            pans.append(pan)
            angles.append(angle)
            print(f"Pan {pan:3d}: Blatt bei {angle:+5.1f}° (offset_x {res['offset_x']:+.2f})")
    finally:
        cam.stop()
        cam.close()

    if len(pans) < 2:
        print("Zu wenige Messungen. Liegt das Blatt gerade vor dem Auto?")
        servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
        return
    slope, intercept = np.polyfit(pans, angles, 1)
    center = -intercept / slope
    print(f"\nLineare Regression: Winkel = {slope:+.3f}°/Einheit * Pan {intercept:+.1f}°")
    print(f"=> Kamera schaut geradeaus bei Pan ≈ {center:.1f}")
    print(f"   (1 Servo-Einheit ≈ {abs(slope):.2f}° Blickwinkel)")
    print(f"   In car_config.py eintragen: PAN_CENTER = {round(center)}")
    servo.setServoPwm(cfg.SERVO_PAN, round(center))


if __name__ == "__main__":
    main()
