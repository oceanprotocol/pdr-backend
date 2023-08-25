import pytest
from unittest.mock import patch, Mock, MagicMock
from pdr_backend.models.contract_data import ContractData
from pdr_backend.models.slot import Slot
from pdr_backend.trueval.main import NewTrueVal, process_slot, main, contract_cache
from pdr_backend.util.web3_config import Web3Config


def test_new_trueval(slot):
    mock_contract_class = mock_contract()
    trueval = NewTrueVal(slot, mock_contract_class, 60)
    result = trueval.run()
    assert result == {"tx": "0x123"}
    mock_contract_class.submit_trueval.assert_called_once_with(
        True, 1692943200, False, True
    )


def test_trueval_main(slot):
    with patch(
        "pdr_backend.trueval.main.PredictoorContract", return_value=mock_contract()
    ) as mock_predictoor_contract:
        result = process_slot(slot, None)
        assert result == {"tx": "0x123"}
        mock_predictoor_contract.assert_called_once_with(None, "0x1")
        mock_predictoor_contract.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, False, True
        )


def test_trueval_main_cached(slot):
    with patch(
        "pdr_backend.trueval.main.PredictoorContract", return_value=mock_contract()
    ) as mock_predictoor_contract:
        process_slot(slot, None)
        process_slot(slot, None)
        assert mock_predictoor_contract.call_count == 1


def test_trueval_with_mocked_price(slot):
    with patch(
        "pdr_backend.trueval.main.PredictoorContract", return_value=mock_contract()
    ) as mock_predictoor_contract:
        with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv):
            result = process_slot(slot, None)
            assert result == {"tx": "0x123"}
            mock_predictoor_contract.return_value.submit_trueval.assert_called_once_with(
                False, 1692943200, False, True
            )


def test_main(slot):
    mocked_env = {
        "RPC_URL": "http://localhost:8545",
        "SUBGRAPH_URL": "http://localhost:9000",
        "PRIVATE_KEY": "0x2b93e10997249bbb0f8daab932f7ed03163ffb2d4c8a2cab02992b92d2ade6ba",
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch("time.sleep"), patch(
        "pdr_backend.trueval.main.get_pending_slots", return_value=[slot]
    ), patch(
        "pdr_backend.trueval.main.Web3Config", return_value=mocked_web3_config
    ), patch(
        "pdr_backend.trueval.main.process_slot"
    ) as ps_mock:
        main(True)

    ps_mock.assert_called_once_with(slot, mocked_web3_config)


# ------------------------------------------------------------
### Fixtures


@pytest.fixture(scope="module")
def slot():
    contract_data = ContractData(
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

    return Slot(
        contract=contract_data,
        slot=1692943200,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    contract_cache.clear()


# ------------------------------------------------------------
### Mocks


def mock_contract(*args, **kwarg):
    m = Mock()
    m.get_secondsPerEpoch.return_value = 60
    m.submit_trueval.return_value = {"tx": "0x123"}
    m.contract_address = "0x1"
    return m


def mock_fetch_ohlcv(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1692943140:
        return [[None, 200]]
    elif since == 1692943200:
        return [[None, 100]]
    else:
        raise ValueError("Invalid timestamp")
