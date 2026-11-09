import http.server
import os
import pathlib
import socketserver
import subprocess
import threading
import time
import urllib.request

PORT = int(os.environ.get("PORT", "10000"))
ROOT = pathlib.Path("/tmp/mix")
ROOT.mkdir(parents=True, exist_ok=True)

BACKING = "https://galam-temp-audio-mix-20261110.onrender.com/backing.mp3"
VOCAL = "https://galam-temp-audio-mix-20261110.onrender.com/vocal.mp3"

STATE = {"status": "starting", "error": None}


def fetch(url, dst):
    last_error = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return
        except Exception as exc:
            last_error = exc
            try:
                dst.unlink(missing_ok=True)
            except Exception:
                pass
            if attempt < 3:
                time.sleep(5 * attempt)
    raise last_error


def ensure_mix():
    backing = ROOT / "backing.mp3"
    vocal = ROOT / "vocal.mp3"
    wav = ROOT / "top_top_rainbow_music_forward_mix.wav"
    mp3 = ROOT / "top_top_rainbow_music_forward_mix.mp3"

    if not backing.exists():
        STATE["status"] = "fetching backing"
        fetch(BACKING, backing)
    if not vocal.exists():
        STATE["status"] = "fetching vocal"
        fetch(VOCAL, vocal)

    if not wav.exists():
        STATE["status"] = "mixing wav"
        fc = (
            "[0:a]aresample=48000,volume=1.00[m];"
            "[1:a]aresample=48000,volume=0.92,asplit=2[vsc][vmix];"
            "[m][vsc]sidechaincompress=threshold=0.08:ratio=2.2:attack=12:release=220[md];"
            "[md][vmix]amix=inputs=2:duration=longest:dropout_transition=3:normalize=0,"
            "alimiter=limit=0.90,loudnorm=I=-16:TP=-1.5:LRA=8[out]"
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(backing), "-i", str(vocal),
                "-filter_complex", fc, "-map", "[out]",
                "-c:a", "pcm_s24le", str(wav),
            ],
            check=True,
        )

    if not mp3.exists():
        STATE["status"] = "encoding mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(wav),
                "-c:a", "libmp3lame", "-b:a", "320k", str(mp3),
            ],
            check=True,
        )

    STATE["status"] = "ready"
    return wav, mp3


def build_mix():
    try:
        ensure_mix()
    except Exception as exc:
        STATE["status"] = "error"
        STATE["error"] = repr(exc)


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.split("?", 1)[0].lstrip("/")
        return str(ROOT / rel)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/status.txt"):
            err = STATE["error"]
            body = (
                ("ready\n" if STATE["status"] == "ready" else f"{STATE['status']}\n")
                if err is None
                else f"error: {err}\n"
            ).encode()
            self.send_response(200 if err is None else 500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


threading.Thread(target=build_mix, daemon=True).start()

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
