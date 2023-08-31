from unittest.mock import patch, MagicMock
from pdr_backend.trueval.main import TruevalAgent, main
from pdr_backend.trueval.trueval_config import TruevalConfig


def test_trueval_main(slot):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch(
        "pdr_backend.models.base_config.Web3Config", return_value=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        main(True)

    ps_mock.assert_called_once_with(slot)
