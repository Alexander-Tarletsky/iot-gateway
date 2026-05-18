# IoT Gateway Worker

Python worker that subscribes to an MQTT topic (AHT10 sensor via ESP32) and forwards readings to an HTTP API.

## Flow

1. Connect to Mosquitto on `127.0.0.1:1883`
2. Subscribe to `home/esp32c3/sensors/aht10`
3. On each message, `POST` JSON to `http://127.0.0.1:8005/test`

## Setup

```bash
cd worker
cp .env.example .env
# Edit .env: MQTT_PASSWORD and other values
```

## Run on host (recommended on macOS)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Uses `127.0.0.1` for both Mosquitto (port `1883` published from its container) and your API on port `8005`.

## Run in Docker (Linux)

Requires Mosquitto with `1883:1883` on the same machine. API should listen on `127.0.0.1:8005`.

```bash
docker compose up --build
```

`network_mode: host` lets the container use the host loopback (`127.0.0.1`).

## Run in Docker (macOS / Docker Desktop)

`network_mode: host` does not share the host network on Mac. Use the Mac compose file and point hosts at the Docker host:

In `.env`:

```
MQTT_HOST=host.docker.internal
API_BASE_URL=http://host.docker.internal:8005
```

```bash
docker compose -f docker-compose.mac.yml up --build
```

Your API can still bind to `127.0.0.1:8005` on the Mac.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_HOST` | `127.0.0.1` | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_TOPIC` | `home/esp32c3/sensors/aht10` | Topic to subscribe |
| `MQTT_USERNAME` | — | Broker username |
| `MQTT_PASSWORD` | — | Broker password |
| `MQTT_CLIENT_ID` | `iot-gateway-worker` | MQTT client id |
| `API_BASE_URL` | `http://127.0.0.1:8005` | API base URL |
| `API_ENDPOINT` | `/test` | API path |
| `HTTP_TIMEOUT_SEC` | `10` | POST timeout |
| `HTTP_RETRY_COUNT` | `2` | Retries after failure |
| `HTTP_RETRY_DELAY_SEC` | `1` | Delay between retries |
| `LOG_LEVEL` | `INFO` | Logging level |

## POST body example

```json
{
  "topic": "home/esp32c3/sensors/aht10",
  "received_at": "2026-05-18T20:15:30.123456+00:00",
  "temperature": 22.49,
  "humidity": 52.17
}
```

## Verify

1. Mosquitto running with ESP32 publishing (test with `mosquitto_sub`).
2. API listening on `127.0.0.1:8005` with `POST /test`.
3. Start the worker; logs should show connect, subscribe, and successful forwards.
