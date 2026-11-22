"""Kamerakopf durch mehrere Winkel fahren und je ein Bild speichern.

Aufruf auf dem Pi:  python3 head_movement_exercise_1.py <kanal> <winkel1> <winkel2> ...
  kanal: 0 = Pan (links/rechts), 1 = Tilt (hoch/runter)
Bilder landen in ~/smartcar/debug/scan_<kanal>_<winkel>.jpg
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

channel = sys.argv[1]
angles = [int(a) for a in sys.argv[2:]]

servo = Servo()
cam = Picamera2()
cam.configure(cam.create_still_configuration(main={"size": (640, 480)}))
cam.start()
try:
    for angle in angles:
        servo.setServoPwm(channel, angle)
        time.sleep(0.8)  # Servo einschwingen lassen
        path = DEBUG / f"scan_{channel}_{angle}.jpg"
        cam.capture_file(str(path))
        print(f"Kanal {channel}, Winkel {angle:3d} -> {path.name}")
finally:
    cam.stop()
    servo.setServoPwm(channel, 90)
    print("Zurück auf 90")
