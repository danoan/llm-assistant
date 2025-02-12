"""
Centralized logging configuration.
"""
import logging.config
from sys import stderr

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s - %(name)s]-[%(levelname)s]: %(message)s",
        },
        "detailed": {
            "format": "[%(asctime)s - %(name)s - %(module)s::%(funcName)s]-[%(levelname)s]: %(message)s",
        },
        "info": {"format": "[%(levelname)s]: %(message)s"},
    },
    "handlers": {
        "stderr": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "info",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "llm-assistant.log",
            "formatter": "detailed",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "danoan.llm_assistant": {
            "level": "INFO",
            "handlers": ["stderr", "file"],
            "propagate": False,
        }
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
