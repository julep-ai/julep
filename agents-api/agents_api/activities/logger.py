import logging
from typing import TextIO

logger: logging.Logger = logging.getLogger(__name__)
h: logging.StreamHandler[TextIO] = logging.StreamHandler()
fmt: logging.Formatter = logging.Formatter("[%(asctime)s/%(levelname)s] - %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)
