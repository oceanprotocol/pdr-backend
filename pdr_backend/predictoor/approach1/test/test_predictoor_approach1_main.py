from unittest.mock import patch, Mock

import pytest

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.predictoor.approach1.main import (  # pylint: disable=unused-import
    process_block,
    log_loop,
    process_topic,
)
from pdr_backend.predictoor.approach1 import main


@pytest.mark.skip(reason="Incomplete, skip")
@patch("pdr_backend.predictoor.approach1.main.get_all_interesting_prediction_contracts")
def test_predictoor_main_process_block(mock_topics):
    mock_topics.return_value = {"0x123": "topic"}

    with patch("pdr_backend.predictoor.approach1.main.process_topic") as mock_pt:
        process_block({"number": 0, "timestamp": 10})
        assert mock_topics.called
        mock_pt.assert_called_with("0x123", 10)


@pytest.mark.skip(reason="Incomplete, skip")
def test_predictoor_main_process_topic(monkeypatch):
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "200")
    main.topics["0x123"] = {
        "name": "topic",
        "address": "0x123",
        "last_submited_epoch": 1,
    }

    mock_contract = Mock(spec=PredictoorContract)
    mock_contract.get_current_epoch.return_value = 2
    mock_contract.get_secondsPerEpoch.return_value = 60
    mock_contract.contract_address = "0x123"

    main.contract_map["0x123"] = mock_contract

    with patch("pdr_backend.predictoor.approach1.main.do_prediction") as mock_dp:
        process_topic("0x123", 10)
        mock_contract.payout.assert_called_with(60, False)
        mock_dp.assert_called_with(
            # last submited epoch is 2 now
            {"name": "topic", "address": "0x123", "last_submited_epoch": 2},
            2,
            mock_contract,
        )
