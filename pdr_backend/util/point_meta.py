from typing import Any,Dict,List

from enforce_typing import enforce_types

@enforce_types
class PointMeta(dict):
    """Defines the bounds for a space, that points can occupy."""
    
    def __init__(self, d: Dict[str,List[Any]]):
        """
        @arguments
          d -- dict of [varname] : cand_vals
        """
        dict.__init__(self, d)
            
    def addVar(self, varname: str, cand_vals:List[any]):
        """Add another variable (dimension) to this space."""
        self[varname] = cand_vals
        
    def n_points(self) -> int:
        """Return # combinations = cross product across all parameters"""
        n_points = 1
        for vals in self.values():
            n_points *= len(vals)
        return n_points

    def point_i(self, i: int) -> Dict[str, Any]:
        """Return point number i"""
        if i < 0 or i >= self.n_points():
            raise ValueError(i)
        multiplier = 1
        point = {}
        for name, cand_vals in self.items():
            point[name] = cand_vals[(i // multiplier) % len(cand_vals)]
            multiplier *= len(cand_vals)
        return point
    
    def __str__(self):
        s = ""
        s += "PointMeta={"
        s += f"{len(self)} vars\n"
        varnames = sorted(self.keys())
        for (i, varname) in enumerate(varnames):
            if len(varnames) > 1: s += "\n   "
            s += f" name={varname}"
            s += f" , cand_vals={self[varname]}"
            if i < len(varnames)-1: s += ", "
            
        if len(varnames) > 1: s += "\n"
        s += "/PointMeta}"
        return s

    
