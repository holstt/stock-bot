import argparse
import logging

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    bot_token: str
    target_guild: int
    tickers: list[str]


def load_config():
    logger.info("Loading config...")
    # Get config path from args
    ap = argparse.ArgumentParser()
    # Optional argument for config file path
    ap.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path of config file",
        default="./config.yml",
    )
    args = vars(ap.parse_args())

    config_path = args["config"]

    # Load config from yaml file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Load into pydantic basemodel
    return AppConfig(**config)
