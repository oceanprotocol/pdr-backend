from enum import Enum

from enforce_typing import enforce_types

class Dirn(Enum):
    UP = 1
    DOWN = 2

UP = Dirn.UP
DOWN = Dirn.DOWN

@enforce_types
def dirn_str(dirn: Dirn):
    if dirn == UP:
        return "UP"
    if dirn == DOWN:
        return "DOWN"
    raise ValueError(dirn)
