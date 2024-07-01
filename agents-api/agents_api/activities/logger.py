import logging


logger = logging.getLogger(__name__)
h = logging.StreamHandler()
fmt = logging.Formatter("[%(asctime)s/%(levelname)s] - %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)
