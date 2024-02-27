"""
Module to setup logging
"""
import logging.config
import os
from string import Template

from yaml import safe_load

from config import BASE_PATH

# logging setup
DEBUG: bool = bool(os.environ.get("WS_DEBUG"))
LEVEL: str = "DEBUG" if DEBUG else "INFO"


def setup_logging() -> None:
    """
    Setup logging from config file with stock template engin
    """
    cfg = BASE_PATH / "logger" / "config.yaml"
    with open(cfg, "r") as fp:
        template = Template(fp.read())
        dictconfig = safe_load(template.substitute(level=LEVEL))
        logging.config.dictConfig(dictconfig)
