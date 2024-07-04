#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import OrderedDict

from enforce_typing import enforce_types


class Point(OrderedDict):

    @enforce_types
    def __str__(self):
        s = "{"
        s += ", ".join([f"{key}={val}" for key, val in self.items()])
        s += "}"
        return s
