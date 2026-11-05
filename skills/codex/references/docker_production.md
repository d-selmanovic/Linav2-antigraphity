# Production Docker Orchestration Reference

## 1. Dockerfile Multi-Stage Best Practices
* Base image: `python:3.11-slim`
* Dependencies: `apt-get install -y --no-install-recommends libasound2 portaudio19-dev libportaudio2 libportaudiocpp0`
* Volume Mounts: Mount `./recordings` as host directory to persist WAV call audio across container restarts.

## 2. Docker Compose
```yaml
version: "3.8"
services:
  lina-voice-agent:
    build: .
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./recordings:/app/recordings
```
