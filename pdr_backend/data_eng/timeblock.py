from enforce_typing import enforce_types
import numpy as np
import pandas as pd


@enforce_types
def timeblock(z, Nt: int) -> pd.DataFrame:
    """
    Calculate a timeblock for training, from a 1-d time series

    @arguments
      z -- 1d array -- timeseries [z(t-Np), z(t-Np+1), ..., z(t-2), z(t-1)]
        where Np == # points in time series == # points back it goes. Eg 500
        so  z[ 0] == z(t-500) is oldest,
        and z[-1] == t(-1) is youngest

      Nt -- int -- # time steps for each input sample. Eg if Nt == 10 then
        at one sample it's   [z(t-13), z(t-12), ..., z(t- 5), z(t- 4)]
        at another sample is [z(t-31), z(t-30), ..., z(t-23), z(t-22)]

    @return
      X -- 2d array -- timeblock [sample i, var j]

      With Nt columns (vars) and Np-Nt rows
      Shaped as:
        [[ z(t-Nt+1)  z(t-Nt+0) ...  z(t-      3)  z(t-      2)
           z(t-Nt+0)  z(t-Nt-1) ...  z(t-      4)  z(t-      3)
           z(t-Nt-1)  z(t-Nt-2) ...  z(t-      5)  z(t-      4)
           ...        ...       ...  ...
           z(t-Np+2)  z(t-Np+3) ...  z(t-Np+Nt+2)  z(t-Np+Nt+1)
           z(t-Np+1)  z(t-Np+2) ...  z(t-Np+Nt+1)  z(t-Np+Nt-0)
           z(t-Np+0)  z(t-Np+1) ...  z(t-Np+Nt-0)  z(t-Np+Nt-1)
    The 0th row is z shifted back by 1 time step
    The 1st row is z shifted back by 2 time steps
    ...
    The nth row is z shifted back by Np-Nt time steps

    It does _not_ give z(t-1) because t-1 is the time "into the future"
    that we're training for.

    Example: if Np = 500, Nt = 10 then it returns X as
      [[ z(t-11)  z(t- 10) ...  z(t-  3)  z(t-  2)
         z(t-12)  z(t- 11) ...  z(t-  4)  z(t-  3)
         ...      ...      ...  ...       ...
         z(t-499) z(t-498) ...  z(t-491)  z(t-490)
         z(t-500) z(t-499) ...  z(t-492)  z(t-491) ]]
    """
    Np = len(z)
    n_rows = Np - Nt
    n_cols = Nt
    X = np.zeros((n_rows, n_cols), dtype=float)
    for row_i in range(n_rows):
        X[row_i, :] = z[-(row_i + Nt + 1) : -(row_i + 1)]
    return X
