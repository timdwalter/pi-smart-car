"""Fahr-Übung 1: vorwärts fahren, kurz anhalten, rückwärts zurück.

Aufruf auf dem Pi:  python3 drive_exercise_1.py [geschwindigkeit=1500] [sekunden=2]
  geschwindigkeit: PWM-Wert pro Motor, 0-4095 (empfohlen 1000-2500)
  sekunden:        Fahrdauer je Richtung

Sicherheit:
  - Vorher: Akkuspannung prüfen (< 6,5 V -> Abbruch)
  - Vorher: Ultraschall prüfen (Hindernis < 30 cm vorne -> Abbruch)
  - Motoren werden IMMER gestoppt: bei Ende, Fehler, Ctrl+C und SIGTERM (z. B. `timeout`)
"""
import signal
import sys
import time

sys.path.insert(0, "/home/pi/Desktop/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server")
from Motor import Motor  # noqa: E402
from ADC import Adc  # noqa: E402

MIN_VOLTAGE = 6.5      # darunter reicht die Kraft nicht zuverlässig
MIN_DISTANCE_CM = 30   # so viel Platz muss vorne frei sein
MAX_SPEED = 3000       # Obergrenze, damit niemand aus Versehen Vollgas gibt


def battery_voltage(adc: Adc) -> float:
    return adc.recvADC(2) * 3


def front_distance_cm():
    """Abstand nach vorne in cm, oder None wenn der Sensor nicht lesbar ist."""
    try:
        from Ultrasonic import Ultrasonic
        return Ultrasonic().get_distance()
    except Exception as e:  # Sensor optional – Übung soll auch ohne laufen
        print(f"  (Ultraschall nicht lesbar: {e})")
        return None


def drive(motor: Motor, adc: Adc, speed: int, seconds: float, label: str):
    print(f"{label}: {seconds:.1f} s mit {speed:+d}")
    motor.setMotorModel(speed, speed, speed, speed)
    t_end = time.time() + seconds
    while time.time() < t_end:
        time.sleep(0.5)
        print(f"  Akku unter Last: {battery_voltage(adc):.2f} V")
    motor.setMotorModel(0, 0, 0, 0)


def main():
    speed = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    speed = max(0, min(abs(speed), MAX_SPEED))

    # SIGTERM (z. B. von `timeout` oder `kill`) wie Ctrl+C behandeln,
    # damit der finally-Block die Motoren stoppt.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    motor = Motor()
    adc = Adc()

    # --- Vorab-Checks ---
    v = battery_voltage(adc)
    print(f"Akku: {v:.2f} V")
    if v < MIN_VOLTAGE:
        print(f"ABBRUCH: Akku unter {MIN_VOLTAGE} V (Motorschalter aus oder Akku leer?)")
        return

    d = front_distance_cm()
    if d is not None:
        print(f"Abstand vorne: {d} cm")
        if 0 < d < MIN_DISTANCE_CM:
            print(f"ABBRUCH: Hindernis näher als {MIN_DISTANCE_CM} cm")
            return

    # --- Fahren ---
    try:
        drive(motor, adc, speed, seconds, "Vorwärts")
        time.sleep(0.5)  # kurz stehen, bevor die Richtung wechselt (schont Motoren und Akku)
        drive(motor, adc, -speed, seconds, "Rückwärts")
        print("Fertig.")
    except KeyboardInterrupt:
        print("Abgebrochen!")
    finally:
        motor.setMotorModel(0, 0, 0, 0)
        print("Motoren gestoppt.")


if __name__ == "__main__":
    main()
