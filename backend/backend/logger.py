import pathlib
import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)
h = logging.StreamHandler()
fmt = logging.Formatter("[%(asctime)s/%(levelname)s] %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)


access_logger = logging.getLogger("access")
log_path = (pathlib.Path(__file__).parent / ".." / "access.log").resolve()
handler = RotatingFileHandler(log_path, maxBytes=50 * 1024 * 1024, backupCount=10)
formatter = logging.Formatter("[%(asctime)s/%(levelname)s] %(message)s")
handler.setFormatter(formatter)
access_logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
