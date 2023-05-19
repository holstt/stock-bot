import logging
import time


def setup_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC
