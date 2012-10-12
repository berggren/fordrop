import logging

log = logging.getLogger()

def init_logging():
    formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    log.addHandler(sh)
    log.setLevel(logging.INFO)
