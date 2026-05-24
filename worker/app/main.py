import logging
import signal
import sys
from queue import Empty, Queue

from dotenv import load_dotenv

from app.api_client import ApiClient
from app.config import load_config
from app.mqtt_client import MqttMessage, MqttSubscriber

load_dotenv()

running = True


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _handle_signal(signum: int, frame: object) -> None:
    global running
    logging.getLogger(__name__).info("Received signal %s, shutting down...", signum)
    running = False


def main() -> int:
    config = load_config()
    _configure_logging(config.log_level)
    logger = logging.getLogger(__name__)

    if not config.climate_api_key:
        logger.error(
            "CLIMATE_API_KEY is not set. Set it in .env to match "
            "Climate Monitor → Settings in Odoo."
        )
        return 1

    message_queue: Queue[MqttMessage] = Queue()
    mqtt_subscriber = MqttSubscriber(config, message_queue)
    api_client = ApiClient(config)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    mqtt_subscriber.start()
    logger.info("Worker started, API target: %s", config.api_url)

    try:
        while running:
            try:
                message = message_queue.get(timeout=1.0)
            except Empty:
                continue
            api_client.forward(message)
    finally:
        mqtt_subscriber.stop()

    logger.info("Worker stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
