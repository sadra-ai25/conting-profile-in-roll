# Profile Counting — Rollway Conveyor

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-green) ![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-red) ![Redis](https://img.shields.io/badge/Redis-Queue-red) ![Docker](https://img.shields.io/badge/Docker-Compose-blue)

Real-time steel profile counting system for rollway (roller conveyor) production lines. Detects and counts steel profiles crossing a virtual horizontal counting line using YOLOv8, with Redis-based frame queuing and shift-based reporting.

## Features

- **Horizontal virtual counting line** — counts profiles crossing `LINE_HORIZONTAL` Y-position
- **YOLOv8 detection** — accurate real-time steel profile detection
- **Redis frame queue** — reliable decoupled producer/consumer architecture
- **RTSP stream support** — connects to any IP camera or MediaMTX relay
- **Configurable reporting window** — hourly or unlimited shift reports
- **REST API** — control stream and query production counts
- **Enhanced structured logging** — with log rotation and configurable levels

## Tech Stack

| Component | Technology |
|---|---|
| AI Model | YOLOv8 (Ultralytics) |
| API Server | FastAPI + Uvicorn |
| Frame Queue | Redis |
| Containerization | Docker Compose |
| Camera Capture | OpenCV |

## Architecture

```
RTSP Camera (top-view of rollway)
      │
      ▼
 Camera Producer (Thread)
   - Captures frames at FRAME_INTERVAL
   - Pushes to Redis queue
      │
      ▼
  Redis Queue
      │
      ▼
 Frame Consumer (Thread)
   - Pulls frames from Redis
   - Runs YOLOv8 detection
   - Checks centroid Y vs. LINE_HORIZONTAL
   - Increments counter on crossing
      │
      ▼
 FastAPI REST API  (counts, reports, shift management)
```

## Prerequisites

- Docker & Docker Compose
- YOLOv8 model weights at `src/ai/weights/best.pt`
- RTSP-capable IP camera

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/sadra-ai25/conting-profile-in-roll.git
cd conting-profile-in-roll

# 2. Configure environment
cp .env.example .env   # edit with your values

# 3. Place model weights
mkdir -p src/ai/weights
cp /path/to/best.pt src/ai/weights/

# 4. Start services
docker compose up -d --build
```

## Configuration

| Key | Description | Example |
|---|---|---|
| `RTSP_URL` | Camera RTSP stream URL | `rtsp://mediamtx:8554/mystream` |
| `LINE_LEFT_X` | Left ROI boundary (X) | `953` |
| `LINE_RIGHT_X` | Right ROI boundary (X) | `1181` |
| `LINE_HORIZONTAL` | Counting line Y-position | `1000` |
| `MODEL_PATH` | YOLOv8 weights path | `/app/src/ai/weights/best.pt` |
| `FRAME_INTERVAL` | Process every Nth frame | `3` |
| `REDIS_HOST` | Redis hostname | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `REPORT_DURATION_HOURS` | Reporting window (`None` = full shift) | `None` |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check and processing status |
| `POST` | `/start` | Start camera stream processing |
| `POST` | `/stop` | Stop camera stream processing |
| `GET` | `/count` | Get current profile count |
| `GET` | `/report` | Get production report for reporting window |
| `POST` | `/reset` | Reset counter for new shift |

### Example: Start Processing

```bash
curl -X POST http://localhost:8000/start
```

### Example: Get Report

```bash
curl http://localhost:8000/report
```

```json
{
  "total_count": 847,
  "report_start": "2024-01-15T07:00:00",
  "report_end": "2024-01-15T15:00:00",
  "duration_hours": 8
}
```

## Difference from LR Conveyor Version

| Feature | LR Conveyor (`conting-profile-lr`) | Rollway (`conting-profile-in-roll`) |
|---|---|---|
| Counting direction | Left → Right (X axis) | Top → Bottom (Y axis) |
| Counting line | Vertical (LINE_LEFT_X, LINE_RIGHT_X) | Horizontal (LINE_HORIZONTAL) |
| Conveyor type | Belt conveyor | Roller (rollway) conveyor |

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT
