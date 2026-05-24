# IoT Gateway Worker

Python worker that subscribes to an MQTT topic (AHT10 sensor via ESP32) and forwards readings to the **Odoo Climate Monitor** HTTP API.

## Flow

```
ESP32 → Mosquitto → this worker → POST /climate/api/v1/readings (Odoo)
```

1. Connect to Mosquitto on `127.0.0.1:1883`
2. Subscribe to `home/esp32c3/sensors/aht10`
3. On each message, `POST` to Odoo with header `X-Climate-Api-Key`

## Setup

```bash
cd worker
cp .env.example .env
```

Edit `.env`:

- `MQTT_PASSWORD` — Mosquitto credentials
- `CLIMATE_API_KEY` — same value as **Climate Monitor → Settings** in Odoo
- `API_BASE_URL` — Odoo base URL (default `http://127.0.0.1:8069`)

## Run on host (recommended on macOS)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Run in Docker (Linux)

```bash
docker compose up --build
```

Uses `network_mode: host` so `127.0.0.1` reaches Mosquitto and Odoo on the same machine.

## Run in Docker (macOS / Docker Desktop)

In `.env`:

```
MQTT_HOST=host.docker.internal
API_BASE_URL=http://host.docker.internal:8069
```

```bash
docker compose -f docker-compose.mac.yml up --build
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_HOST` | `127.0.0.1` | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_TOPIC` | `home/esp32c3/sensors/aht10` | Topic to subscribe |
| `MQTT_USERNAME` | — | Broker username |
| `MQTT_PASSWORD` | — | Broker password |
| `MQTT_CLIENT_ID` | `iot-gateway-worker` | MQTT client id |
| `API_BASE_URL` | `http://127.0.0.1:8069` | Odoo base URL |
| `API_ENDPOINT` | `/climate/api/v1/readings` | Ingestion path |
| `CLIMATE_API_KEY` | — | **Required.** `X-Climate-Api-Key` header |
| `DEVICE_ID` | `esp32` | Default `device_id` if not in MQTT JSON |
| `HTTP_TIMEOUT_SEC` | `10` | POST timeout |
| `HTTP_RETRY_COUNT` | `2` | Retries after failure |
| `HTTP_RETRY_DELAY_SEC` | `1` | Delay between retries |
| `LOG_LEVEL` | `INFO` | Logging level |

## MQTT payload (from ESP32)

```json
{"temperature": 22.49, "humidity": 52.17}
```

Optional fields: `device_id`, `timestamp` or `reading_time` (Unix, ISO, or Odoo format).

## POST body sent to Odoo

```json
{
  "device_id": "esp32",
  "temperature": 22.49,
  "humidity": 52.17,
  "timestamp": "2026-05-23 12:00:00"
}
```

`timestamp` is always sent: from the device payload if present, otherwise from the time the worker received the MQTT message. Format is **naive UTC** `YYYY-MM-DD HH:MM:SS` as required by Climate Monitor (no `T` or `Z` suffix).

## Verify

1. Odoo running with **Climate Monitor** installed and API key configured.
2. Mosquitto running; ESP32 publishing (or test with `mosquitto_pub`).
3. Start the worker; logs should show connect, subscribe, and `Forwarded ... id=N`.

Test with curl (same contract as the worker):

```bash
curl -X POST http://127.0.0.1:8069/climate/api/v1/readings \
  -H "Content-Type: application/json" \
  -H "X-Climate-Api-Key: your-key" \
  -d '{"device_id":"esp32","temperature":22.5,"humidity":48.2,"timestamp":"2026-05-23 12:00:00"}'
```
