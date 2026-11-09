import pathlib
import subprocess
import urllib.request

import imageio_ffmpeg

ROOT = pathlib.Path("public")
TMP = pathlib.Path(".mix_tmp")
ROOT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

BACKING_URL = "https://galam-temp-audio-mix-20261110.onrender.com/backing.mp3"
VOCAL_URL = "https://galam-temp-audio-mix-20261110.onrender.com/vocal.mp3"

backing = TMP / "backing.mp3"
vocal = TMP / "vocal.mp3"
output = ROOT / "top_top_rainbow_music_forward_mix.mp3"


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as response, open(path, "wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)


download(BACKING_URL, backing)
download(VOCAL_URL, vocal)

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
filters = (
    "[0:a]aresample=48000,volume=0.94[m];"
    "[1:a]aresample=48000,volume=1.10,asplit=2[vsc][vmix];"
    "[m][vsc]sidechaincompress=threshold=0.08:ratio=2.2:attack=12:release=220[md];"
    "[md][vmix]amix=inputs=2:duration=longest:dropout_transition=3:normalize=0,"
    "alimiter=limit=0.90,loudnorm=I=-16:TP=-1.5:LRA=8[out]"
)

subprocess.run(
    [
        ffmpeg,
        "-y",
        "-i", str(backing),
        "-i", str(vocal),
        "-filter_complex", filters,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        str(output),
    ],
    check=True,
)

(ROOT / "status.txt").write_text("ready\n", encoding="utf-8")
print(f"built {output} ({output.stat().st_size} bytes)")
