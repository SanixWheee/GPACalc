import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger object with the given name.

    Parameters
    ----------
    name: str

    Returns
    -------
    logging.Logger
    """
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    log.addHandler(handler)

    return log
