from typing import Dict
from unittest.mock import patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import (
    Prediction,
    fetch_contract_id_and_spe,
    fetch_filtered_predictions,
    get_all_contract_ids_by_owner,
)
from pdr_backend.util.time_types import UnixTimeS

ADA_CONTRACT_ADDRESS = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"

SAMPLE_PREDICTION = Prediction(
    # pylint: disable=line-too-long
    ID="0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1698527100-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    contract="0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
    pair="ADA-USDT",
    timeframe="5m",
    predvalue=True,
    stake=0.050051425480971974,
    truevalue=False,
    timestamp=UnixTimeS(1698527000),
    source="binance",
    payout=0.0,
    slot=UnixTimeS(1698527100),
    user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
)

# pylint: disable=line-too-long
_PREDICTION = {
    "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1698527100-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    "user": {"id": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"},
    "stake": "0.050051425480971974",
    "timestamp": 1698527000,
    "payout": {"payout": "0", "trueValue": False, "predictedValue": True},
    "slot": {
        "slot": 1698527100,
        "predictContract": {
            "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
            "secondsPerEpoch": "300",
            "token": {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                "name": "ADA-USDT",
                "nft": {
                    "nftData": [
                        {
                            "key": "0x238ad53218834f943da60c8bafd36c36692dcb35e6d76bdd93202f5c04c0baff",
                            "value": "0x55534454",
                        },
                        {
                            "key": "0x2cef5778d97683b4f64607f72e862fc0c92376e44cc61195ef72a634c0b1793e",
                            "value": "0x4144412f55534454",
                        },
                        {
                            "key": "0x49435d2ff85f9f3594e40e887943d562765d026d50b7383e76891f8190bff4c9",
                            "value": "0x356d",
                        },
                        {
                            "key": "0xf1f3eb40f5bc1ad1344716ced8b8a0431d840b5783aea1fd01786bc26f35ac0f",
                            "value": "0x414441",
                        },
                        {
                            "key": "0xf7e3126f87228afb82c9b18537eed25aaeb8171a78814781c26ed2cfeff27e69",
                            "value": "0x62696e616e6365",
                        },
                    ]
                },
            },
        },
    },
}

MOCK_PREDICTIONS_RESPONSE_FIRST_CALL = {"data": {"predictPredictions": [_PREDICTION]}}

MOCK_PREDICTIONS_RESPONSE_SECOND_CALL: Dict[str, dict] = {}

MOCK_PREDICTIONS_RESPONSE_1000 = {
    "data": {"predictPredictions": [_PREDICTION for i in range(0, 1000)]}
}

MOCK_CONTRACTS_RESPONSE = {
    "data": {
        "tokens": [
            {"id": "token1"},
            {"id": "token2"},
        ]
    }
}

MOCK_CONTRACT_DETAILS_RESPONSE = {
    "data": {
        "predictContracts": [
            {"id": "contract1", "secondsPerEpoch": 300, "token": {"name": "token1"}},
            {"id": "contract2", "secondsPerEpoch": 600, "token": {"name": "token2"}},
        ]
    }
}


@enforce_types
@patch("pdr_backend.subgraph.subgraph_predictions.query_subgraph")
def test_fetch_filtered_predictions(mock_query_subgraph):
    """
    @description
      Test that fetch_filtered_predictions() can fetch predictions from subgraph
      and return them as a list of Prediction objects.
    """
    # show the system can fetch multiple times, and handle empty responses
    mock_query_subgraph.side_effect = [
        MOCK_PREDICTIONS_RESPONSE_1000,
        MOCK_PREDICTIONS_RESPONSE_1000,
        MOCK_PREDICTIONS_RESPONSE_SECOND_CALL,
    ]
    predictions = fetch_filtered_predictions(
        start_ts=UnixTimeS(1622547000),
        end_ts=UnixTimeS(1622548800),
        first=1000,
        skip=0,
        addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        network="mainnet",
    )

    assert len(predictions) == 1000
    assert isinstance(predictions[0], Prediction)
    assert predictions[0].user == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"
    assert predictions[0].pair == "ADA/USDT"
    assert predictions[0].contract == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"
    assert predictions[0].truevalue is False
    assert predictions[0].predvalue is True
    assert mock_query_subgraph.call_count == 1


@enforce_types
@patch("pdr_backend.subgraph.subgraph_predictions.query_subgraph")
def test_fetch_filtered_predictions_exception(mock_query_subgraph):
    """
    @description
        Verifies that fetch_filtered_predictions() can handle exceptions from subgraph
        and return the predictions that were fetched before the exception.
    """
    num_successful_fetches = 1

    # we're going to simulate an exception from subgraph on the second call
    # pylint: disable=unused-argument
    def simulate_exception(*args, **kwargs):
        if simulate_exception.call_count < num_successful_fetches:
            simulate_exception.call_count += 1
            return MOCK_PREDICTIONS_RESPONSE_1000
        raise Exception(f"Simulated exception on call #{num_successful_fetches+1}")

    simulate_exception.call_count = 0

    # Patch query_subgraph to use our simulate_exception function
    mock_query_subgraph.side_effect = simulate_exception

    predictions = fetch_filtered_predictions(
        start_ts=UnixTimeS(1622547000),
        end_ts=UnixTimeS(1622548800),
        first=1000,
        skip=0,
        addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        network="mainnet",
    )

    assert len(predictions) == num_successful_fetches * 1000
    assert mock_query_subgraph.call_count == num_successful_fetches


@enforce_types
def test_fetch_filtered_predictions_no_data():
    # network not supported
    with pytest.raises(Exception):
        fetch_filtered_predictions(
            start_ts=UnixTimeS(1622547000),
            end_ts=UnixTimeS(1622548800),
            first=1000,
            skip=0,
            addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="xyz",
        )

    with patch(
        "pdr_backend.subgraph.subgraph_predictions.query_subgraph"
    ) as mock_query_subgraph:
        mock_query_subgraph.return_value = {"data": {}}
        predictions = fetch_filtered_predictions(
            start_ts=UnixTimeS(1622547000),
            end_ts=UnixTimeS(1622548800),
            first=1000,
            skip=0,
            addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="mainnet",
        )
    assert len(predictions) == 0

    with patch(
        "pdr_backend.subgraph.subgraph_predictions.query_subgraph"
    ) as mock_query_subgraph:
        mock_query_subgraph.return_value = {"data": {"predictPredictions": []}}
        predictions = fetch_filtered_predictions(
            start_ts=UnixTimeS(1622547000),
            end_ts=UnixTimeS(1622548800),
            first=1000,
            skip=0,
            addresses=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="mainnet",
        )
    assert len(predictions) == 0


@enforce_types
@patch(
    "pdr_backend.subgraph.subgraph_predictions.query_subgraph",
    return_value=MOCK_CONTRACTS_RESPONSE,
)
def test_get_all_contract_ids_by_owner(
    mock_query_subgraph,
):  # pylint: disable=unused-argument
    contract_ids = get_all_contract_ids_by_owner(
        owner_address="0xOwner", network="mainnet"
    )

    assert len(contract_ids) == 2
    assert "token1" in contract_ids
    assert "token2" in contract_ids
    mock_query_subgraph.assert_called_once()

    with patch(
        "pdr_backend.subgraph.subgraph_predictions.query_subgraph",
        return_value={"data": {}},
    ):
        with pytest.raises(Exception):
            get_all_contract_ids_by_owner(owner_address="0xOwner", network="mainnet")

    # network not supported
    with pytest.raises(Exception):
        get_all_contract_ids_by_owner(owner_address="0xOwner", network="xyz")


@enforce_types
@patch(
    "pdr_backend.subgraph.subgraph_predictions.query_subgraph",
    return_value=MOCK_CONTRACT_DETAILS_RESPONSE,
)
def test_fetch_contract_id_and_spe(
    mock_query_subgraph,
):  # pylint: disable=unused-argument
    contracts_list = fetch_contract_id_and_spe(
        contract_addresses=["contract1", "contract2"], network="mainnet"
    )

    assert len(contracts_list) == 2

    c0, c1 = contracts_list  # pylint: disable=unbalanced-tuple-unpacking
    assert c0["ID"] == "contract1"
    assert c0["seconds_per_epoch"] == 300
    assert c0["name"] == "token1"
    assert c1["ID"] == "contract2"
    assert c1["seconds_per_epoch"] == 600
    assert c1["name"] == "token2"

    mock_query_subgraph.assert_called_once()

    with patch(
        "pdr_backend.subgraph.subgraph_predictions.query_subgraph",
        return_value={"data": {}},
    ):
        with pytest.raises(Exception):
            fetch_contract_id_and_spe(
                contract_addresses=["contract1", "contract2"], network="mainnet"
            )

    # network not supported
    with pytest.raises(Exception):
        fetch_contract_id_and_spe(
            contract_addresses=["contract1", "contract2"], network="xyz"
        )
