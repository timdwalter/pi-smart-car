"""CV-Übung 1: grünes Blatt Papier im Kamerabild erkennen.

Aufruf auf dem Pi:  python3 cv_exercise_1.py [tilt] [pan]
  tilt: Kanal 0, Standard 90 (Suchen). pan: Kanal 1, Standard 90 (Mitte)

Vorgehen:
  1. Kamera per Servo ausrichten, ein Bild aufnehmen
  2. In den HSV-Farbraum umrechnen und alle grünen Pixel maskieren
  3. Rauschen per Morphologie entfernen, größte grüne Fläche suchen
  4. Schwerpunkt, Bounding-Box und horizontale Abweichung von der Bildmitte ausgeben

Ausgaben in ~/smartcar/debug/:
  cv1_raw.jpg      Originalbild
  cv1_mask.jpg     Grün-Maske (weiß = grün)
  cv1_overlay.jpg  Originalbild mit eingezeichneter Erkennung
"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
DEBUG.mkdir(parents=True, exist_ok=True)

# HSV-Grenzen für Grün (OpenCV: H 0-179, S 0-255, V 0-255)
GREEN_LOW = np.array([35, 35, 40])     # S ab 35: bei Kunstlicht (57 Lux, 2430 K) hat das Blatt aus 150 cm
                                       # nur S ~48 (Median). Mit S >= 60 blieben nur Krümel übrig.
                                       # Der Boden (H 0-18) ist weit weg vom Grün, das bleibt unkritisch.
GREEN_HIGH = np.array([95, 255, 255])  # Blatt ist blaugrün (H ~80-87), Blau beginnt ~100
MIN_AREA_FRACTION = 0.0005  # kleinere Flecken werden ignoriert (0,05 % des Bildes = 154 Pixel).
                            # Ursprünglich 0,2 %, dann 0,1 %: Das Blatt aus 150 cm (~300-470 Pixel) lag genau an
                            # der Grenze und wurde mal erkannt, mal nicht. Fehlalarme fängt der Horizont-Filter ab.


def capture(tilt: int, pan: int) -> np.ndarray:
    servo = Servo()
    servo.setServoPwm("0", tilt)
    servo.setServoPwm("1", pan)
    time.sleep(0.8)
    cam = Picamera2()
    cam.configure(cam.create_still_configuration(main={"size": (640, 480), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)  # Belichtung/Weißabgleich einschwingen
    frame = cam.capture_array()  # RGB888 liefert BGR-Reihenfolge -> passt zu OpenCV
    cam.stop()
    cam.close()
    return frame


def detect_green(frame: np.ndarray, accept=None):
    """Größte grüne Fläche finden.

    accept: optionale Funktion accept(bbox) -> bool. Dann wird die größte Fläche genommen,
    die diesen Test besteht (z. B. "flach und unterhalb des Horizonts" = Blatt auf dem Boden).
    So gewinnt ein Lichtreflex nicht, nur weil er größer ist als das Blatt.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)
    # 3x3 statt 5x5: Aus 150 cm ist das Blatt nur ein ~5-6 Pixel hoher Streifen,
    # ein 5x5-Öffnen würde ihn größtenteils wegfressen.
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # kleine Störpunkte weg
    # Löcher und Lücken im Blatt schließen. Breiter, flacher Filter (5 hoch, 15 breit): Ein fernes Blatt
    # ist ein flacher Streifen, den Lichtreflexe in Stücke teilen - die waagerechten Lücken werden überbrückt.
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 15), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return mask, None
    candidates = sorted(contours, key=cv2.contourArea, reverse=True)
    if accept is not None:
        candidates = [c for c in candidates if accept(cv2.boundingRect(c))]
        if not candidates:
            return mask, None
    biggest = candidates[0]
    h, w = mask.shape
    area = cv2.contourArea(biggest)
    if area < MIN_AREA_FRACTION * w * h:
        return mask, None

    m = cv2.moments(biggest)
    cx, cy = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
    return mask, {
        "contour": biggest,
        "center": (cx, cy),
        "bbox": cv2.boundingRect(biggest),
        "area_fraction": area / (w * h),
        # -1 = ganz links, 0 = Mitte, +1 = ganz rechts
        "offset_x": (cx - w / 2) / (w / 2),
        # 0 = oberer Bildrand (weit weg), 1 = unterer Bildrand (nah)
        "pos_y": cy / h,
    }


def draw(frame: np.ndarray, result) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    cv2.line(out, (w // 2, 0), (w // 2, h), (255, 255, 255), 1)  # Bildmitte
    if result is None:
        cv2.putText(out, "KEIN GRUEN", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        return out
    cv2.drawContours(out, [result["contour"]], -1, (0, 0, 255), 2)
    x, y, bw, bh = result["bbox"]
    cv2.rectangle(out, (x, y), (x + bw, y + bh), (255, 0, 0), 1)
    cv2.circle(out, result["center"], 6, (0, 0, 255), -1)
    cv2.line(out, (w // 2, result["center"][1]), result["center"], (0, 255, 255), 2)
    text = f"offset_x={result['offset_x']:+.2f}  pos_y={result['pos_y']:.2f}  flaeche={result['area_fraction']*100:.1f}%"
    cv2.putText(out, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return out


def main():
    tilt = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    pan = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    frame = capture(tilt, pan)
    mask, result = detect_green(frame)

    cv2.imwrite(str(DEBUG / "cv1_raw.jpg"), frame)
    cv2.imwrite(str(DEBUG / "cv1_mask.jpg"), mask)
    cv2.imwrite(str(DEBUG / "cv1_overlay.jpg"), draw(frame, result))

    print(f"Kamera: tilt={tilt} pan={pan}")
    if result is None:
        print("Ergebnis: KEIN grünes Blatt erkannt")
        return
    side = "Mitte" if abs(result["offset_x"]) < 0.1 else ("rechts" if result["offset_x"] > 0 else "links")
    print("Ergebnis: grünes Blatt erkannt")
    print(f"  Schwerpunkt:   {result['center']} px")
    print(f"  Bounding-Box:  {result['bbox']} (x, y, b, h)")
    print(f"  Fläche:        {result['area_fraction']*100:.1f} % des Bildes")
    print(f"  offset_x:      {result['offset_x']:+.2f} -> liegt {side}")
    print(f"  pos_y:         {result['pos_y']:.2f} (0 = weit weg/oben, 1 = nah/unten)")


if __name__ == "__main__":
    main()
