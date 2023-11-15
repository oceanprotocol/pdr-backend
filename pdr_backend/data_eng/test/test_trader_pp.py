from enforce_typing import enforce_types

from pdr_backend.data_eng.trader_pp import TraderPP


@enforce_types
def test_trader_pp():
    d = {"sim_only":
         {"fee_percent" : 0.01,
          "init_holdings" : ['10000.0 USDT', '0 BTC'],
          }
         }
    pp = TraderPP(d)

    # yaml properteis
    assert pp.fee_percent == 0.01
    assert pp.init_holdings_strs == ['10000.0 USDT', '0 BTC']

    # derivative properties
    assert pp.init_holdings["USDT"] == 10000.0
    assert "TraderPP" in str(pp)
    assert "fee_percent" in str(pp)

    # str
    assert "TraderPP" in str(pp)
