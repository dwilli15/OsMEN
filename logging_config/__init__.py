"""Project logging helpers."""

import logging.config
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def configure_logging():
    if CONFIG_PATH.exists():
        logging.config.fileConfig(CONFIG_PATH)
    else:
        logging.basicConfig(level=logging.INFO)
