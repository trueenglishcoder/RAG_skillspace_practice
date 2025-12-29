"""Точка входа для учебной версии бота."""

from __future__ import annotations

import asyncio
import logging

from .bot import run_bot

logging.basicConfig(level=logging.INFO)


def main() -> None:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logging.info("Остановка по Ctrl+C")


if __name__ == "__main__":
    main()
