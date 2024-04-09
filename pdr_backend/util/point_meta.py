from collections import OrderedDict

from enforce_typing import enforce_types

from pdr_backend.util.point import Point


class PointMeta(OrderedDict):
    """Defines the bounds for a space, that points can occupy."""

    @property
    def n_points(self) -> int:
        """Return # combinations = cross product across all parameters"""
        n_points = 1
        for vals in self.values():
            n_points *= len(vals)
        return n_points

    @enforce_types
    def point_i(self, i: int) -> Point:
        """
        @description
          Return point #i.

        @return
          point -- OrderedDict, with vars in the same order as self

        @notes
          We traverse in a very precise order, using integer division & mod.
          The end result: the code is compact, and we cover all the points.
        """
        if i < 0 or i >= self.n_points:
            raise ValueError(i)
        multiplier = 1
        point = Point()
        for name, cand_vals in self.items():
            point[name] = cand_vals[(i // multiplier) % len(cand_vals)]
            multiplier *= len(cand_vals)
        return point

    @enforce_types
    def __str__(self):
        s = ""
        s += "PointMeta={"
        s += f"{len(self)} vars\n"
        varnames = sorted(self.keys())
        for i, varname in enumerate(varnames):
            if len(varnames) > 1:
                s += "\n   "
            s += f" name={varname}"
            s += f" , cand_vals={self[varname]}"
            if i < len(varnames) - 1:
                s += ", "

        if len(varnames) > 1:
            s += "\n"
        s += "/PointMeta}"
        return s
