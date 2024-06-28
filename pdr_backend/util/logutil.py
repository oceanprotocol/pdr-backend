#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging


def logging_has_stdout():
    return any(
        isinstance(handler, logging.StreamHandler)
        for handler in logging._handlers.values()
    )
