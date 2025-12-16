import logging
from logging.config import dictConfig


def setup_logging():
    logging_config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
    dictConfig(logging_config)


setup_logging()

logger = logging.getLogger("autosentinels")
