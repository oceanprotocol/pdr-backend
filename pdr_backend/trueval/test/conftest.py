import os
from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.models.contract_data import ContractData
from pdr_backend.models.slot import Slot


@pytest.fixture()
def slot():
    contract_data = ContractData(
        name="ETH-USDT",
        address="0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    return Slot(
        contract=contract_data,
        slot=1692943200,
    )


@pytest.fixture(autouse=True)
def set_env_vars():
    original_value = os.environ.get("OWNER_ADDRS", None)
    os.environ["OWNER_ADDRS"] = "0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e"
    yield
    if original_value is not None:
        os.environ["OWNER_ADDRS"] = original_value
    else:
        os.environ.pop("OWNER_ADDRS", None)
