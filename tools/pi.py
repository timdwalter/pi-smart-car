"""SSH-Helfer für den Raspberry Pi. Liest PI_HOST/PI_USER/PI_PASSWORD aus .env.

Benutzung:
    python tools/pi.py run "<befehl>"            # Befehl auf dem Pi ausführen
    python tools/pi.py put <lokal> <remote>      # Datei hochladen
    python tools/pi.py get <remote> <lokal>      # Datei herunterladen
"""
import os
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def connect() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=os.environ["PI_HOST"],
        username=os.environ["PI_USER"],
        password=os.environ.get("PI_PASSWORD") or None,
        timeout=10,
    )
    return client


def run(cmd: str) -> int:
    with connect() as c:
        _, stdout, stderr = c.exec_command(cmd)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        code = stdout.channel.recv_exit_status()
    sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return code


def put(local: str, remote: str) -> int:
    with connect() as c, c.open_sftp() as sftp:
        sftp.put(local, remote)
    return 0


def get(remote: str, local: str) -> int:
    with connect() as c, c.open_sftp() as sftp:
        sftp.get(remote, local)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    action, *args = sys.argv[1:]
    sys.exit({"run": lambda: run(" ".join(args)),
              "put": lambda: put(*args),
              "get": lambda: get(*args)}[action]())
