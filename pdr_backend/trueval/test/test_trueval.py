from unittest.mock import patch
from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.models.contract_data import ContractData


def mock_fetch_ohlcv(pair, timeframe, since, limit):
    if since == 1:
        return [[None, 100]]
    elif since == 2:
        return [[None, 200]]
    else:
        raise ValueError("Invalid timestamp")


def mock_fetch_ohlcv_fail(pair, timeframe, since, limit):
    return []


def test_get_trueval_success():
    contract = ContractData(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv):
        result = get_true_val(contract, 1, 2)
        assert result == (True, False)  # True because 200 > 100


def test_get_trueval_fail():
    contract = ContractData(
        name="ETH-USDT",
        address="0x1",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_fail):
        result = get_true_val(contract, 1, 2)
        assert result == (False, True)  # True because failed
