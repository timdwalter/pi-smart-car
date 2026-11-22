"""Dreh-Übung 1: auf der Stelle um einen Winkel drehen, gemessen mit der Kamera.

Das Auto hat keine Drehgeber und keinen Kompass. Deshalb misst die Kamera die
Drehung selbst ("visuelle Odometrie"):

  1. Foto A aufnehmen
  2. kurz drehen (Impuls), anhalten
  3. Foto B aufnehmen
  4. markante Punkte (ORB-Features) in A und B finden und einander zuordnen
  5. aus der horizontalen Verschiebung der Punkte den Drehwinkel berechnen
  6. Winkel aufaddieren, bis das Ziel erreicht ist. Den nächsten Impuls aus der
     bisher gemessenen Drehgeschwindigkeit so bemessen, dass nicht überdreht wird.

Aufruf auf dem Pi:  python3 turn_exercise_1.py [winkel=90] [richtung=links|rechts] [speed=2000]
  speed=0 -> Trockenlauf: Motoren bleiben aus, nur die Bildmessung wird getestet

Debug-Bilder in ~/smartcar/debug/: turn_start.jpg, turn_end.jpg, turn_matches_<n>.jpg
"""
import math
import signal
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from Motor import Motor  # noqa: E402
from ADC import Adc  # noqa: E402
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

W, H = 640, 480
HFOV_DEG = 53.5                                   # horizontaler Bildwinkel der OV5647
FOCAL_PX = (W / 2) / math.tan(math.radians(HFOV_DEG / 2))  # Brennweite in Pixeln

MIN_VOLTAGE = 6.5
FIRST_PULSE_S = 0.25      # erster Impuls: kurz, um die Drehgeschwindigkeit zu messen
MAX_PULSE_S = 0.3         # nie länger am Stück drehen: ~18°, Bilder müssen sich deutlich überlappen
MIN_PULSE_S = 0.08        # kürzere Impulse bewegen das Auto kaum (Haftreibung)
MAX_STEPS = 25
MAX_FAILS = 2             # so viele Fehlmessungen hintereinander werden geschätzt, dann Abbruch
TOLERANCE_DEG = 3.0
MIN_MATCHES = 15
ROI_TOP_FRACTION = 0.55   # nur obere 55 % des Bildes nutzen: Wände/Möbel statt Boden.
                          # Der Boden ist sehr nah (starke Parallaxe) und spiegelt (Reflexe wandern mit).


def grab(cam) -> np.ndarray:
    time.sleep(0.4)  # nach dem Anhalten: Wackeln abklingen lassen, frisches Bild
    return cam.capture_array()


def measure_rotation(img_a, img_b, step: int):
    """Drehwinkel zwischen zwei Bildern in Grad (+ = Szene nach rechts = Auto nach links)."""
    orb = cv2.ORB_create(nfeatures=1500)
    ga, gb = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    roi = np.zeros_like(ga)
    roi[: int(H * ROI_TOP_FRACTION), :] = 255
    kp_a, des_a = orb.detectAndCompute(ga, roi)
    kp_b, des_b = orb.detectAndCompute(gb, roi)
    if des_a is None or des_b is None:
        return None, 0
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(des_a, des_b)
    matches = sorted(matches, key=lambda m: m.distance)[:200]
    if len(matches) < MIN_MATCHES:
        return None, len(matches)

    # Winkel jedes Punktes zur Bildmitte vorher/nachher -> Differenz = Drehung
    angles = []
    for m in matches:
        xa = kp_a[m.queryIdx].pt[0] - W / 2
        xb = kp_b[m.trainIdx].pt[0] - W / 2
        angles.append(math.degrees(math.atan(xb / FOCAL_PX) - math.atan(xa / FOCAL_PX)))
    angles = np.array(angles)
    median = float(np.median(angles))
    # Ausreißer (Fehlzuordnungen) ignorieren. Die Toleranz wächst mit dem Winkel, weil nahe
    # Objekte durch Parallaxe (Kamera sitzt vor der Drehachse) etwas weiter wandern als ferne.
    tol = max(2.5, 0.25 * abs(median))
    good = np.abs(angles - median) < tol
    inliers = int(np.sum(good))
    if inliers < MIN_MATCHES:
        print(f"    (Diagnose: {len(kp_a)}/{len(kp_b)} Punkte, {len(matches)} Zuordnungen, "
              f"Median {median:+.1f}°, nur {inliers} innerhalb ±{tol:.1f}°)")
        return None, inliers

    vis = cv2.drawMatches(img_a, kp_a, img_b, kp_b, matches[:40], None, flags=2)
    cv2.imwrite(str(DEBUG / f"turn_matches_{step}.jpg"), vis)
    return float(np.median(angles[good])), inliers


def main():
    target = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
    direction = sys.argv[2] if len(sys.argv) > 2 else "links"
    speed = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    sign = 1 if direction == "links" else -1
    dry_run = speed == 0

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    motor, adc, servo = Motor(), Adc(), Servo()
    v = adc.recvADC(2) * 3
    print(f"Akku: {v:.2f} V")
    if v < MIN_VOLTAGE and not dry_run:
        print(f"ABBRUCH: Akku unter {MIN_VOLTAGE} V")
        return

    # Kamera geradeaus: Wände und Möbel liefern viele markante Punkte
    servo.setServoPwm("0", 80)
    servo.setServoPwm("1", 90)

    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)

    def turn(seconds: float):
        if dry_run:
            time.sleep(seconds)
            return
        s = speed * sign
        motor.setMotorModel(-s, -s, s, s)   # links: linke Räder zurück, rechte vor
        time.sleep(seconds)
        motor.setMotorModel(0, 0, 0, 0)

    total = 0.0
    fails = 0
    pulse = FIRST_PULSE_S
    rate = None  # gemessene Grad pro Sekunde Impuls
    print(f"Ziel: {target:.0f}° nach {direction}  (speed={speed}{', TROCKENLAUF' if dry_run else ''})")
    try:
        prev = grab(cam)
        cv2.imwrite(str(DEBUG / "turn_start.jpg"), prev)
        for step in range(1, MAX_STEPS + 1):
            turn(pulse)
            cur = grab(cam)
            angle, n = measure_rotation(prev, cur, step)
            if angle is None:
                fails += 1
                if rate is None or fails > MAX_FAILS:
                    print(f"Schritt {step}: Messung fehlgeschlagen ({n} Punkte). ABBRUCH.")
                    break
                # Fallback: Winkel aus der bisher gemessenen Drehrate schätzen
                angle = rate * pulse
                total += angle
                print(f"Schritt {step}: Impuls {pulse:.2f} s -> ~{angle:4.1f}° GESCHÄTZT "
                      f"(nur {n} Punkte; Summe {total:5.1f}°)")
                prev = cur
                remaining = target - total
                if remaining <= TOLERANCE_DEG:
                    break
                pulse = max(MIN_PULSE_S, min(MAX_PULSE_S, 0.8 * remaining / rate))
                continue
            fails = 0
            angle *= sign  # in Drehrichtung positiv
            total += angle
            if angle > 0.5:
                step_rate = angle / pulse
                rate = step_rate if rate is None else 0.5 * rate + 0.5 * step_rate
            rate_txt = f"{rate:.0f}°/s" if rate is not None else "-"
            print(f"Schritt {step}: Impuls {pulse:.2f} s -> {angle:+5.1f}°  "
                  f"(Summe {total:5.1f}°, {n} Punkte, Rate {rate_txt})")
            prev = cur

            remaining = target - total
            if remaining <= TOLERANCE_DEG:
                break
            if dry_run:
                if step >= 3:
                    break
                continue
            if rate is None:
                pulse = min(pulse * 1.5, MAX_PULSE_S)  # hat sich kaum bewegt -> länger
            else:
                # 80 % des Rests anpeilen, damit eher unter- als überdreht wird
                pulse = max(MIN_PULSE_S, min(MAX_PULSE_S, 0.8 * remaining / rate))
        print(f"Ergebnis: {total:.1f}° gedreht (Ziel {target:.0f}°, Abweichung {total - target:+.1f}°)")
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        cv2.imwrite(str(DEBUG / "turn_end.jpg"), cam.capture_array())
        cam.stop()
        cam.close()
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
