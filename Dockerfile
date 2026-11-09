FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY server.py /app/server.py
ENV PORT=10000
CMD ["python","/app/server.py"]
