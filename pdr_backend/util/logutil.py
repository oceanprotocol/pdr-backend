import logging


def logging_has_stdout():
    return any(
        isinstance(handler, logging.StreamHandler)
        for handler in logging._handlers.values()
    )
