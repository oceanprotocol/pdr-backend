from unittest.mock import patch, MagicMock
from pdr_backend.trueval.main import TruevalAgent, main
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.constants import ZERO_ADDRESS


def test_trueval_main_1(slot):
    mocked_web3_config = MagicMock()

    with patch(
        "pdr_backend.models.base_config.Web3Config", return_value=mocked_web3_config
    ), patch("time.sleep"), patch(
        "pdr_backend.trueval.main.sys.argv", [0, "1"]
    ), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        main(True)

    ps_mock.assert_called_once_with(slot)


def test_trueval_main_2():
    mocked_web3_config = MagicMock()

    with patch(
        "pdr_backend.models.base_config.Web3Config", return_value=mocked_web3_config
    ), patch("time.sleep"), patch(
        "pdr_backend.trueval.main.get_address", return_value=ZERO_ADDRESS
    ), patch(
        "pdr_backend.trueval.main.sys.argv", [0, "2"]
    ), patch.object(
        TruevalAgentBatch, "take_step"
    ) as ts_mock:
        main(True)

    ts_mock.assert_called_once()
