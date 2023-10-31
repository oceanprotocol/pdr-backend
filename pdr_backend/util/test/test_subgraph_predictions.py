import unittest
from unittest.mock import patch, Mock
from pdr_backend.util.subgraph_predictions import (
    get_all_predictions,
    FilterMode,
)  # Adjust the import based on where you have saved the function


class TestGetAllPredictions(unittest.TestCase):
    @patch("pdr_backend.util.subgraph_predictions.query_subgraph")
    @patch("pdr_backend.util.subgraph_predictions.get_subgraph_url")
    @patch("pdr_backend.util.subgraph_predictions.info_from_725")
    def test_contract_filter_mode(
        self, mock_info_from_725, mock_get_subgraph_url, mock_query_subgraph
    ):
        mock_query_subgraph.return_value = {"data": {"predictPredictions": []}}
        mock_get_subgraph_url.return_value = "mock_url"
        mock_info_from_725.return_value = {
            "pair": "BTC/USD",
            "timeframe": "1h",
            "source": "MockSource",
        }
        get_all_predictions(
            0, 10, ["contract1", "contract2"], "mainnet", FilterMode.CONTRACT
        )
        self.assertTrue(
            mock_query_subgraph.called, "Expected query_subgraph to be called."
        )
        called_args = mock_query_subgraph.call_args_list[0][1]["query"]
        self.assertIn("predictContract_in", called_args)

    @patch("pdr_backend.util.subgraph_predictions.query_subgraph")
    @patch("pdr_backend.util.subgraph_predictions.get_subgraph_url")
    @patch("pdr_backend.util.subgraph_predictions.info_from_725")
    def test_predictoor_filter_mode(
        self, mock_info_from_725, mock_get_subgraph_url, mock_query_subgraph
    ):
        mock_query_subgraph.return_value = {"data": {"predictPredictions": []}}
        mock_get_subgraph_url.return_value = "mock_url"
        mock_info_from_725.return_value = {
            "pair": "BTC/USD",
            "timeframe": "1h",
            "source": "MockSource",
        }
        get_all_predictions(0, 10, ["user1", "user2"], "mainnet", FilterMode.PREDICTOOR)
        self.assertTrue(
            mock_query_subgraph.called, "Expected query_subgraph to be called."
        )
        called_args = mock_query_subgraph.call_args_list[0][1]["query"]
        self.assertIn("id_in", called_args)

    @patch("pdr_backend.util.subgraph_predictions.query_subgraph")
    @patch("pdr_backend.util.subgraph_predictions.get_subgraph_url")
    def test_invalid_network(self, mock_get_subgraph_url, mock_query_subgraph):
        with self.assertRaises(Exception):
            get_all_predictions(
                0, 10, ["user1"], "invalid_network", FilterMode.PREDICTOOR
            )


if __name__ == "__main__":
    unittest.main()
