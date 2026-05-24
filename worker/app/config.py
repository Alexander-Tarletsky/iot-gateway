import os
from dataclasses import dataclass
from urllib.parse import urljoin

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class Config:
    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_username: str
    mqtt_password: str
    mqtt_client_id: str
    api_base_url: str
    api_endpoint: str
    climate_api_key: str
    device_id: str
    http_timeout_sec: float
    http_retry_count: int
    http_retry_delay_sec: float
    log_level: str

    @property
    def api_url(self) -> str:
        base = self.api_base_url.rstrip("/") + "/"
        path = self.api_endpoint.lstrip("/")
        return urljoin(base, path)


def load_config() -> Config:
    return Config(
        mqtt_host=os.getenv("MQTT_HOST", "127.0.0.1"),
        mqtt_port=_get_int("MQTT_PORT", 1883),
        mqtt_topic=os.getenv("MQTT_TOPIC", "home/esp32c3/sensors/aht10"),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "iot-gateway-worker"),
        api_base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8069"),
        api_endpoint=os.getenv("API_ENDPOINT", "/climate/api/v1/readings"),
        climate_api_key=os.getenv("CLIMATE_API_KEY", ""),
        device_id=os.getenv("DEVICE_ID", "esp32"),
        http_timeout_sec=_get_float("HTTP_TIMEOUT_SEC", 10.0),
        http_retry_count=_get_int("HTTP_RETRY_COUNT", 2),
        http_retry_delay_sec=_get_float("HTTP_RETRY_DELAY_SEC", 1.0),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
