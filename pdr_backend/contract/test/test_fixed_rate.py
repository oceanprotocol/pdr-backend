from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.contract.fixed_rate import FixedRate
from pdr_backend.util.currency_types import Eth, Wei


@enforce_types
def test_FixedRate(predictoor_contract, web3_pp):
    exchanges = predictoor_contract.get_exchanges()
    print(exchanges)

    address = exchanges[0][0]
    exchangeId = exchanges[0][1]

    # constructor
    exchange = FixedRate(web3_pp, address)

    # test get_dt_price()
    tup = exchange.get_dt_price(exchangeId)
    (
        baseTokenAmt_wei,
        oceanFeeAmt_wei,
        publishMktFeeAmt_wei,
        consumeMktFeeAmt_wei,
    ) = tup

    assert baseTokenAmt_wei.to_eth().amt_eth == approx(3.603)

    assert oceanFeeAmt_wei.amt_eth == approx(0.003)
    assert publishMktFeeAmt_wei.amt_eth == approx(0.6)
    assert consumeMktFeeAmt_wei.amt_eth == 0

    # test calcBaseInGivenOutDT()
    tup2 = exchange.calcBaseInGivenOutDT(exchangeId, Eth(1).to_wei(), Wei(0))
    assert tup == tup2
