"""Project logging helpers."""

import logging
import logging.config
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def configure_logging():
    if CONFIG_PATH.exists():
        try:
            logging.config.fileConfig(CONFIG_PATH)
        except Exception:  # pragma: no cover - fallback when config invalid
            logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
