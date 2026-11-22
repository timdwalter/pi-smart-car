"""Boden-Kalibrierung: Welche Bildzeile entspricht welchem Abstand auf dem Boden?

Das grüne Blatt wird mit seiner VORDEREN Kante auf einen bekannten Abstand gelegt,
gemessen ab der VORDERKANTE DES AUTOS (Lineal-Wert). Das Skript rechnet
car_config.LENS_BEHIND_FRONT_CM dazu, intern zählt der Abstand ab dem Punkt unter der Linse. Das Skript sucht die Unterkante des Blattes
im Bild und speichert das Paar (Abstand, Bildzeile).

Ab zwei Messpunkten werden Kamerahöhe h und Neigung alpha berechnet (Lochkamera-Modell):

    Winkel unter der Bildmitte:   beta(y) = atan((y - H/2) / f)
    Bodenabstand:                 d(y)    = h / tan(alpha + beta(y))

Daraus folgt der tote Winkel = Abstand am unteren Bildrand (y = H).

Aufruf auf dem Pi:
  python3 ground_calibration.py messen <abstand_ab_autokante_cm> [tilt=110]
  python3 ground_calibration.py auswerten
  python3 ground_calibration.py reset
"""
import json
import math
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from servo import Servo  # noqa: E402
from picamera2 import Picamera2  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_exercise_1 import detect_green, draw  # noqa: E402
from turn_exercise_1 import FOCAL_PX, W, H  # noqa: E402
import car_config as cfg  # noqa: E402

DEBUG = Path.home() / "smartcar" / "debug"
STORE = Path.home() / "smartcar" / "ground_calibration.json"


def load():
    return json.loads(STORE.read_text()) if STORE.exists() else []


def messen(dist_cm: float, tilt: int):
    servo = Servo()
    servo.setServoPwm(cfg.SERVO_TILT, tilt)
    servo.setServoPwm(cfg.SERVO_PAN, cfg.PAN_CENTER)
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"}))
    cam.start()
    time.sleep(1.5)
    frame = cam.capture_array()
    cam.stop()
    cam.close()

    mask, res = detect_green(frame)
    out = draw(frame, res)
    if res is None:
        cv2.imwrite(str(DEBUG / f"ground_{dist_cm:g}cm.jpg"), out)
        print("Kein Blatt erkannt!")
        return
    # Vordere Blattkante in der BILDMITTE messen (dort liegt das Lineal). Die Bounding-Box
    # würde den tiefsten Punkt irgendwo nehmen - bei leicht schräger Kante also eine Ecke.
    col = mask[:, W // 2 - 5: W // 2 + 5]
    rows = [r for r in range(H) if col[r].any()]
    if not rows:
        print("Blatt erkannt, aber nicht in der Bildmitte!")
        cv2.imwrite(str(DEBUG / f"ground_{dist_cm:g}cm.jpg"), out)
        return
    edge_y = max(rows)  # unterste grüne Zeile in der Mitte = vordere Blattkante
    cv2.line(out, (0, edge_y), (W, edge_y), (255, 0, 255), 1)
    cv2.imwrite(str(DEBUG / f"ground_{dist_cm:g}cm.jpg"), out)
    if edge_y >= H - 2:
        print(f"Unterkante bei y={edge_y}: Das Blatt reicht bis an den Bildrand, die Kante liegt im toten Winkel!")
        return
    d_lens = dist_cm + cfg.LENS_BEHIND_FRONT_CM
    pts = [p for p in load() if not (p["front"] == dist_cm and p["tilt"] == tilt)]
    pts.append({"front": dist_cm, "d": d_lens, "y": edge_y, "tilt": tilt})
    STORE.write_text(json.dumps(pts, indent=1))
    print(f"Messpunkt gespeichert: {dist_cm:g} cm ab Autokante ({d_lens:g} cm ab Linse) "
          f"-> Bildzeile y={edge_y} (Tilt {tilt})")


def model(y, h, alpha, f):
    """Bodenabstand (ab Linse) für Bildzeile y."""
    ang = alpha + math.atan((y - H / 2) / f)
    return h / math.tan(ang) if ang > 0 else float("inf")


def solve(pts, f=FOCAL_PX):
    """Kamerahöhe h und Neigung alpha bei fester Brennweite f (kleinste Quadrate, Rasterung).

    Erkenntnis aus der Kalibrierung: Mit Messpunkten nur im Nahbereich lassen sich Höhe und
    Brennweite NICHT sauber trennen (5 cm hoch + lange Brennweite erklärt die Punkte fast genauso
    gut wie 9 cm hoch + kurze Brennweite). Deshalb wird die Brennweite festgehalten - sie ist
    durch Übung 4 (Drehen) unabhängig bestätigt - und die Höhe mitbestimmt.
    """
    best = None
    for h100 in range(300, 1500, 5):
        h = h100 / 100
        for a100 in range(500, 6000, 10):
            alpha = math.radians(a100 / 100)
            err = sum((model(p["y"], h, alpha, f) - p["d"]) ** 2 for p in pts)
            if best is None or err < best[0]:
                best = (err, alpha, h)
    return best


def auswerten():
    pts = load()
    for tilt in sorted({p["tilt"] for p in pts}):
        tp = sorted((p for p in pts if p["tilt"] == tilt), key=lambda p: p["d"])
        print(f"Tilt {tilt}: " + ", ".join(f"{p['d']:g} cm -> y={p['y']}" for p in tp))
        if len(tp) < 2:
            print("  mindestens 2 Messpunkte nötig (besser 3)")
            continue
        f = FOCAL_PX
        err, alpha, h = solve(tp, f)
        bottom = model(H, h, alpha, f)
        print(f"  Brennweite f = {f:.0f} px (fest), Kamerahöhe h ≈ {h:.2f} cm, "
              f"Neigung ≈ {math.degrees(alpha):.1f}° unter waagerecht")
        print(f"  Restfehler: {math.sqrt(err / len(tp)):.2f} cm (RMS)")
        print(f"  => TOTER WINKEL (unterer Bildrand) ≈ {bottom:.1f} cm ab Kameralinse "
              f"= {bottom - cfg.LENS_BEHIND_FRONT_CM:.1f} cm ab Autokante")
        for p in tp:
            pred = model(p["y"], h, alpha, f)
            print(f"     Kontrolle {p['d']:g} cm: Modell sagt {pred:.1f} cm")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auswerten"
    if cmd == "messen":
        messen(float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else cfg.TILT_NEAR)
    elif cmd == "reset":
        STORE.unlink(missing_ok=True)
        print("Messpunkte gelöscht.")
    else:
        auswerten()
