from unittest.mock import MagicMock, Mock, patch
from pdr_backend.trueval.main import main
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_agent_single import TruevalAgentSingle
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.constants import ZERO_ADDRESS
from pdr_backend.util.web3_config import Web3Config


def test_trueval_main_1(slot):
    mocked_web3_config = Mock(spec=Web3Config)
    mocked_web3_config.get_block = Mock()
    mocked_web3_config.get_block.return_value = {"timestamp": 0}
    mocked_web3_config.w3 = MagicMock()

    with patch(
        "pdr_backend.models.base_config.Web3Config", return_value=mocked_web3_config
    ), patch(
        "pdr_backend.trueval.trueval_agent_single.wait_until_subgraph_syncs"
    ), patch(
        "time.sleep"
    ), patch(
        "pdr_backend.trueval.main.sys.argv", [0, "1"]
    ), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgentSingle, "process_slot"
    ) as ps_mock:
        main(True)

    ps_mock.assert_called_once_with(slot)


def test_trueval_main_2():
    mocked_web3_config = Mock(spec=Web3Config)
    mocked_web3_config.get_block = Mock()
    mocked_web3_config.get_block.return_value = {"timestamp": 0}
    mocked_web3_config.w3 = MagicMock()

    with patch(
        "pdr_backend.models.base_config.Web3Config", return_value=mocked_web3_config
    ), patch("pdr_backend.trueval.main.get_address", return_value=ZERO_ADDRESS), patch(
        "pdr_backend.trueval.main.sys.argv", [0, "2"]
    ), patch.object(
        TruevalAgentBatch, "take_step"
    ) as ts_mock:
        main(True)

    ts_mock.assert_called_once()
