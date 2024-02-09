import logging


logger = logging.getLogger(__name__)
h = logging.StreamHandler()
f = logging.Formatter("[%(asctime)s/%(levelname)s] - %(message)s")
h.setFormatter(f)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)
