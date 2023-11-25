from unittest.mock import patch

from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.dfbuyer.main import main


@patch.object(DFBuyerAgent, "run")
@patch.object(
    DFBuyerAgent, "__init__", return_value=None
)  # Mock the constructor to return None
def test_main(mock_agent_init, mock_agent_run):
    main()
    mock_agent_init.assert_called_once()
    mock_agent_run.assert_called_once()
