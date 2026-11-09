FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/public /tmp/mix

RUN curl -fL --retry 5 --retry-delay 3 --connect-timeout 20 --max-time 180 \
      https://galam-temp-audio-mix-20261110.onrender.com/backing.mp3 \
      -o /tmp/mix/backing.mp3 \
    && curl -fL --retry 5 --retry-delay 3 --connect-timeout 20 --max-time 180 \
      https://galam-temp-audio-mix-20261110.onrender.com/vocal.mp3 \
      -o /tmp/mix/vocal.mp3 \
    && ffmpeg -y \
      -i /tmp/mix/backing.mp3 \
      -i /tmp/mix/vocal.mp3 \
      -filter_complex "[0:a]aresample=48000,volume=1.00[m];[1:a]aresample=48000,volume=0.92,asplit=2[vsc][vmix];[m][vsc]sidechaincompress=threshold=0.08:ratio=2.2:attack=12:release=220[md];[md][vmix]amix=inputs=2:duration=longest:dropout_transition=3:normalize=0,alimiter=limit=0.90,loudnorm=I=-16:TP=-1.5:LRA=8[out]" \
      -map "[out]" \
      -c:a libmp3lame -b:a 320k \
      /app/public/top_top_rainbow_music_forward_mix.mp3 \
    && printf "ready\n" > /app/public/status.txt \
    && rm -rf /tmp/mix

COPY server.py /app/server.py
ENV PORT=10000
CMD ["python","/app/server.py"]
