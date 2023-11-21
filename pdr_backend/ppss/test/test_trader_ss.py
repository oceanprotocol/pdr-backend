from enforce_typing import enforce_types

from pdr_backend.ppss.trader_ss import TraderSS


@enforce_types
def test_trader_ss():
    d = {
        "sim_only": {
            "buy_amt": "10 USD",
        },
        "bot_only": {
            "min_buffer": 60,
            "max_tries": 10,
            "position_size" : 3
        },
    }
    ss = TraderSS(d)

    # yaml properties
    assert ss.buy_amt_str == "10 USD"
    assert ss.min_buffer == 60
    assert ss.max_tries == 10
    assert ss.position_size == 3

    # derivative properties
    assert ss.buy_amt_usd == 10.0


    # setters
    ss.set_max_tries(12)
    assert ss.max_tries == 12

    ss.set_min_buffer(59)
    assert ss.min_buffer == 59

    ss.set_position_size(15)
    assert ss.position_size == 15

    # str
    assert "TraderSS" in str(ss)
