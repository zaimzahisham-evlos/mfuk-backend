import logging
from enum import StrEnum

class LogLevel(StrEnum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"
    exception = "EXCEPTION"

LOG_FORMAT_DEBUG = "[%(levelname)s] - %(asctime)s: %(pathname)s:%(funcName)s:%(lineno)d - %(message)s"

def setup_logging(level: LogLevel = LogLevel.info):
    level_str = str(level).upper()
    levels = [level.value for level in LogLevel]

    if level_str not in levels:
        logging.basicConfig(level=LogLevel.error)
        return

    if level == LogLevel.debug:
        logging.basicConfig(level=level_str, format=LOG_FORMAT_DEBUG)
        return

    logging.basicConfig(level=level_str)
