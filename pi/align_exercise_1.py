"""Übung 5: Grünes Blatt suchen und das Auto darauf ausrichten.

Kombiniert die Bausteine aus den vorherigen Übungen:
  - Grün-Erkennung       (cv_exercise_1.detect_green)
  - Drehen per Impulsen  (wie turn_exercise_1)
  - Drehwinkel messen    (turn_exercise_1.measure_rotation) -> nur in der Suchphase

Ablauf (schrittweise, Stop-and-Go):
  SUCHEN:      Kein Blatt im Bild -> einen Impuls in Suchrichtung drehen. Mitzählen,
               wie weit gedreht wurde (visuelle Odometrie). Nach 360° aufgeben.
  AUSRICHTEN:  Blatt im Bild -> Winkel zum Blatt direkt aus dem Bild berechnen
               (offset_x -> Lochkamera-Modell) und einen passenden Impuls drehen.
               Fertig, wenn das Blatt höchstens TOLERANCE_DEG neben der Bildmitte liegt.

Aufruf auf dem Pi:  python3 align_exercise_1.py [suchrichtung=rechts|links] [speed=2000]
  speed=0 -> Trockenlauf: nur ein Bild auswerten, Motoren bleiben aus

Debug-Bilder in ~/smartcar/debug/: align_<schritt>.jpg (Overlay der Erkennung je Schritt)
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
from turn_exercise_1 import measure_rotation, FOCAL_PX, W, H  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

MIN_VOLTAGE = 6.5
TOLERANCE_DEG = 3.0       # so genau soll das Blatt mittig liegen
SEARCH_PULSE_S = 0.3      # Suchimpuls (~15°), Bilder überlappen noch für die Odometrie
MAX_PULSE_S = 0.3
MIN_PULSE_S = 0.08
START_RATE = 55.0         # °/s, Startwert für die Drehrate (aus Übung 4), wird nachgeführt
MAX_SEARCH_DEG = 360.0
MAX_STEPS = 40


def offset_to_angle(offset_x: float) -> float:
    """offset_x (-1..+1) -> Winkel in Grad zur Blickrichtung (+ = rechts)."""
    x_px = offset_x * (W / 2)
    return math.degrees(math.atan(x_px / FOCAL_PX))


def main():
    search_dir = sys.argv[1] if len(sys.argv) > 1 else "rechts"
    speed = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    dry_run = speed == 0

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    motor, adc, servo = Motor(), Adc(), Servo()
    v = adc.recvADC(2) * 3
    print(f"Akku: {v:.2f} V")
    if v < MIN_VOLTAGE and not dry_run:
        print(f"ABBRUCH: Akku unter {MIN_VOLTAGE} V")
        return

    servo.setServoPwm(cfg.SERVO_TILT, cfg.TILT_SEARCH)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)  # wirklich geradeaus, nicht 90!
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)

    def grab():
        time.sleep(0.4)  # nach dem Anhalten Wackeln abklingen lassen
        return cam.capture_array()

    def turn(direction: str, seconds: float):
        """direction 'rechts' oder 'links', kurzer Impuls, danach Stopp."""
        if dry_run:
            return
        s = speed if direction == "links" else -speed
        motor.setMotorModel(-s, -s, s, s)
        time.sleep(seconds)
        motor.setMotorModel(0, 0, 0, 0)

    rate = START_RATE
    searched = 0.0
    found_once = False
    print(f"Suche Blatt, Suchrichtung {search_dir}{' (TROCKENLAUF)' if dry_run else ''}")
    try:
        frame = grab()
        for step in range(1, MAX_STEPS + 1):
            _, result = detect_green(frame)
            cv2.imwrite(str(DEBUG / f"align_{step:02d}.jpg"), draw(frame, result))

            if result is not None:
                # ---------- AUSRICHTEN ----------
                found_once = True
                angle = offset_to_angle(result["offset_x"])
                print(f"Schritt {step}: Blatt gesehen, {angle:+5.1f}° "
                      f"({'rechts' if angle > 0 else 'links'}), pos_y={result['pos_y']:.2f}, "
                      f"Fläche {result['area_fraction']*100:.1f} %")
                if abs(angle) <= TOLERANCE_DEG:
                    print(f"AUSGERICHTET: Blatt liegt {angle:+.1f}° neben der Mitte.")
                    break
                if dry_run:
                    break
                pulse = max(MIN_PULSE_S, min(MAX_PULSE_S, 0.8 * abs(angle) / rate))
                turn("rechts" if angle > 0 else "links", pulse)
                new = grab()
                # Drehrate nachführen: am Blatt selbst ablesen, wie weit es gewandert ist
                _, r2 = detect_green(new)
                if r2 is not None:
                    moved = abs(angle - offset_to_angle(r2["offset_x"]))
                    if moved > 1.0:
                        rate = 0.5 * rate + 0.5 * (moved / pulse)
                frame = new
            else:
                # ---------- SUCHEN ----------
                if found_once:
                    print(f"Schritt {step}: Blatt aus dem Bild verloren -> weiter suchen")
                if dry_run:
                    print("Trockenlauf: kein Blatt im Bild.")
                    break
                if searched >= MAX_SEARCH_DEG:
                    print(f"ABBRUCH: {searched:.0f}° gesucht, kein Blatt gefunden.")
                    break
                turn(search_dir, SEARCH_PULSE_S)
                new = grab()
                measured, n = measure_rotation(frame, new, step)
                if measured is None:
                    measured = rate * SEARCH_PULSE_S  # Schätzung wie in Übung 4
                    how = "geschätzt"
                else:
                    measured = abs(measured)
                    rate = 0.5 * rate + 0.5 * (measured / SEARCH_PULSE_S)
                    how = f"{n} Punkte"
                searched += measured
                print(f"Schritt {step}: kein Blatt -> {search_dir} gedreht ~{measured:4.1f}° "
                      f"({how}), gesamt gesucht {searched:5.1f}°")
                frame = new
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
