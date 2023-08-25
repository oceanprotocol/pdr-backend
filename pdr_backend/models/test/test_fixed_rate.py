from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.models.fixed_rate import FixedRate


@enforce_types
def test_FixedRate(predictoor_contract, web3_config):
    exchanges = predictoor_contract.get_exchanges()
    address = exchanges[0][0]
    id_ = exchanges[0][1]
    print(exchanges)
    rate = FixedRate(web3_config, address)
    assert rate.get_dt_price(id_)[0] / 1e18 == approx(3.603)
