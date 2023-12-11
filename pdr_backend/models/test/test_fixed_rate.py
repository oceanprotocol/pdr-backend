from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.models.fixed_rate import FixedRate
from pdr_backend.util.wei import from_wei


@enforce_types
def test_FixedRate(predictoor_contract, web3_pp):
    exchanges = predictoor_contract.get_exchanges()
    print(exchanges)

    address = exchanges[0][0]
    exchangeId = exchanges[0][1]

    exchange = FixedRate(web3_pp, address)

    (
        baseTokenAmt_wei,
        oceanFeeAmt_wei,
        publishMktFeeAmt_wei,
        consumeMktFeeAmt_wei,
    ) = exchange.get_dt_price(exchangeId)

    assert from_wei(baseTokenAmt_wei) == approx(3.603)

    assert from_wei(oceanFeeAmt_wei) == approx(0.003)
    assert from_wei(publishMktFeeAmt_wei) == approx(0.6)
    assert consumeMktFeeAmt_wei == 0
