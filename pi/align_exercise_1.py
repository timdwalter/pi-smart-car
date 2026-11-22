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
TOLERANCE_DEG = 4.0       # so genau soll das Blatt mittig liegen. 3° führte zum Pendeln: Der kürzeste
                          # Impuls (0,08 s) dreht wegen Haftreibung/Nachlauf ~8° statt 4°.
SEARCH_PULSE_S = 0.3      # Suchimpuls (~15°), Bilder überlappen noch für die Odometrie
MAX_PULSE_S = 0.3
MIN_PULSE_S = 0.08
START_RATE = 55.0         # °/s, Startwert für die Drehrate (aus Übung 4), wird nachgeführt
MAX_SEARCH_DEG = 360.0
MAX_STEPS = 40
# Horizont-Filter: Ein Blatt AUF DEM BODEN liegt im Bild unterhalb der Wand/Möbel-Linie.
# Grüne Flächen, deren Unterkante weiter oben liegt (Bücher im Regal, Pflanzen ...), werden ignoriert.
MIN_EDGE_Y_FRACTION = 0.15  # y=72. Ein Versuch mit 0.25 sortierte das echte Blatt aus: Der wacklige Kamerakopf
                            # verschiebt den Horizont um Dutzende Pixel. Die Hauptarbeit macht der Formfilter.
# Formfilter: Ein flach liegendes Blatt ist aus der niedrigen Kameraperspektive immer deutlich
# BREITER als hoch. Lichtreflexe auf dem Laminat und Fensterflecken sind dagegen hoch und schmal.
MIN_ASPECT = 1.5


def looks_like_sheet(bbox) -> bool:
    """Blatt auf dem Boden: Unterkante unterhalb des Horizonts UND breiter als hoch."""
    x, y, w, h = bbox
    return (y + h) >= MIN_EDGE_Y_FRACTION * H and w >= MIN_ASPECT * h


def offset_to_angle(offset_x: float) -> float:
    """offset_x (-1..+1) -> Winkel in Grad zur Blickrichtung (+ = rechts)."""
    x_px = offset_x * (W / 2)
    return math.degrees(math.atan(x_px / FOCAL_PX))


def open_camera():
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)
    return cam


def align(cam, motor, search_dir: str = "rechts", speed: int = 2000, dry_run: bool = False,
          prefix: str = "align") -> bool:
    """Blatt suchen und das Auto darauf ausrichten. True, wenn ausgerichtet.

    Erwartet Kamera auf TILT_SEARCH / PAN_CENTER. Wird auch von mission_exercise_1.py genutzt."""

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
    last_seen_dir = None  # wo das Blatt zuletzt war -> dorthin suchen, wenn es verloren geht
    rechecked = False     # wurde nach einem Verlust schon ein zweites Foto gemacht?
    print(f"Suche Blatt, Suchrichtung {search_dir}{' (TROCKENLAUF)' if dry_run else ''}")
    frame = grab()
    for step in range(1, MAX_STEPS + 1):
        _, any_green = detect_green(frame)
        _, result = detect_green(frame, accept=looks_like_sheet)
        if any_green is not None and result is None:
            x, y, bw, bh = any_green["bbox"]
            print(f"Schritt {step}: grüne Fläche ignoriert (pos_y={any_green['pos_y']:.2f}, "
                  f"{bw}x{bh} px): über dem Horizont oder nicht flach -> kein Blatt")
        cv2.imwrite(str(DEBUG / f"{prefix}_{step:02d}.jpg"), draw(frame, result))

        if result is not None:
            # ---------- AUSRICHTEN ----------
            found_once = True
            rechecked = False
            angle = offset_to_angle(result["offset_x"])
            last_seen_dir = "rechts" if angle > 0 else "links"
            print(f"Schritt {step}: Blatt gesehen, {angle:+5.1f}° "
                  f"({'rechts' if angle > 0 else 'links'}), pos_y={result['pos_y']:.2f}, "
                  f"Fläche {result['area_fraction']*100:.1f} %")
            if abs(angle) <= TOLERANCE_DEG:
                print(f"AUSGERICHTET: Blatt liegt {angle:+.1f}° neben der Mitte.")
                return True
            if dry_run:
                return False
            pulse = max(MIN_PULSE_S, min(MAX_PULSE_S, 0.8 * abs(angle) / rate))
            turn("rechts" if angle > 0 else "links", pulse)
            new = grab()
            # Drehrate nachführen: am Blatt selbst ablesen, wie weit es gewandert ist
            _, r2 = detect_green(new, accept=looks_like_sheet)
            if r2 is not None:
                moved = abs(angle - offset_to_angle(r2["offset_x"]))
                if moved > 1.0:
                    rate = 0.5 * rate + 0.5 * (moved / pulse)
            frame = new
        else:
            # ---------- SUCHEN ----------
            if found_once and last_seen_dir is not None and not rechecked:
                # Gerade eben noch gesehen? Erst ein zweites Foto machen, bevor gesucht wird:
                # Bei kleinen, fernen Flächen flackert die Erkennung manchmal für ein einzelnes Bild.
                rechecked = True
                print(f"Schritt {step}: Blatt kurz verloren -> zweites Foto ohne zu drehen")
                frame = grab()
                continue
            rechecked = False
            if found_once:
                print(f"Schritt {step}: Blatt aus dem Bild verloren -> weiter suchen")
            if dry_run:
                print("Trockenlauf: kein Blatt im Bild.")
                return False
            if searched >= MAX_SEARCH_DEG:
                print(f"ABBRUCH: {searched:.0f}° gesucht, kein Blatt gefunden.")
                return False
            # Verloren? Dann zuerst dorthin drehen, wo es zuletzt war - nicht stur in Suchrichtung.
            direction = last_seen_dir or search_dir
            turn(direction, SEARCH_PULSE_S)
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
            print(f"Schritt {step}: kein Blatt -> {direction} gedreht ~{measured:4.1f}° "
                  f"({how}), gesamt gesucht {searched:5.1f}°")
            frame = new
    print(f"ABBRUCH: maximal {MAX_STEPS} Schritte erreicht.")
    return False


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
    cam = open_camera()
    try:
        align(cam, motor, search_dir, speed, dry_run)
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
