import http.server, socketserver, os, subprocess, urllib.request, pathlib

PORT = int(os.environ.get("PORT", "10000"))
ROOT = pathlib.Path("/tmp/mix")
ROOT.mkdir(parents=True, exist_ok=True)

BACKING = "https://v3b.fal.media/files/b/0ab1d277/vg3azhCbiCttox9mvMJ0y_top_top_rainbow_126bpm.mp3"
VOCAL = "https://v3b.fal.media/files/b/0ab1d2af/Wnck4_AqAdz_H6ZPS_kt8_160336189849601-9XQwy3UgoMKRfod4Z3hHUc.mp3"

def fetch(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
        while True:
            chunk = r.read(1024*1024)
            if not chunk:
                break
            f.write(chunk)

def ensure_mix():
    backing = ROOT/"backing.mp3"
    vocal = ROOT/"vocal.mp3"
    wav = ROOT/"top_top_rainbow_music_forward_mix.wav"
    mp3 = ROOT/"top_top_rainbow_music_forward_mix.mp3"
    if not backing.exists():
        fetch(BACKING, backing)
    if not vocal.exists():
        fetch(VOCAL, vocal)
    if not wav.exists():
        fc = (
            "[0:a]aresample=48000,volume=1.00[m];"
            "[1:a]aresample=48000,volume=0.92,asplit=2[vsc][vmix];"
            "[m][vsc]sidechaincompress=threshold=0.08:ratio=2.2:attack=12:release=220[md];"
            "[md][vmix]amix=inputs=2:duration=longest:dropout_transition=3:normalize=0,"
            "alimiter=limit=0.90,loudnorm=I=-16:TP=-1.5:LRA=8[out]"
        )
        subprocess.run([
            "ffmpeg","-y","-i",str(backing),"-i",str(vocal),
            "-filter_complex",fc,"-map","[out]",
            "-c:a","pcm_s24le",str(wav)
        ], check=True)
    if not mp3.exists():
        subprocess.run([
            "ffmpeg","-y","-i",str(wav),
            "-c:a","libmp3lame","-b:a","320k",str(mp3)
        ], check=True)
    return wav, mp3

ERROR = None
try:
    ensure_mix()
except Exception as e:
    ERROR = repr(e)

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.lstrip("/")
        return str(ROOT/rel)
    def do_GET(self):
        if self.path in ("/","/status.txt"):
            body = ("ok\\n" if ERROR is None else "error: "+ERROR+"\\n").encode()
            self.send_response(200 if ERROR is None else 500)
            self.send_header("Content-Type","text/plain; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
