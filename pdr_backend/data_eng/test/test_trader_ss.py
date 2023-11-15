from enforce_typing import enforce_types

from pdr_backend.data_eng.trader_ss import TraderSS


@enforce_types
def test_trader_ss():
    d = {"sim_only":
         {"buy_amt": "10 USD",
          }
         }
    ss = TraderSS(d)

    # yaml properties
    assert ss.buy_amt_str == "10 USD"

    # derivative properties
    assert ss.buy_amt_usd == 10.0

    # str
    assert "TraderSS" in str(ss)
