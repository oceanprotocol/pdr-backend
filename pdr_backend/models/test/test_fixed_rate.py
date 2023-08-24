
def test_FixedRate(predictoor_contract, web3_config):
    exchanges = predictoor_contract.get_exchanges()
    address = exchanges[0][0]
    id = exchanges[0][1]
    print(exchanges)
    rate = FixedRate(web3_config, address)
    assert rate.get_dt_price(id)[0] / 1e18 == approx(3.603)
