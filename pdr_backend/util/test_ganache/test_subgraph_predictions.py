from typing import Dict
from unittest.mock import patch
from enforce_typing import enforce_types
from pdr_backend.util.subgraph_predictions import (
    fetch_filtered_predictions,
    get_all_contract_ids_by_owner,
    fetch_contract_id_and_spe,
    FilterMode,
    Prediction,
)

SAMPLE_PREDICTION = Prediction(
    pair="ADA/USDT",
    timeframe="5m",
    prediction=True,
    stake=0.050051425480971974,
    trueval=False,
    timestamp=1698527100,
    source="binance",
    payout=0.0,
    user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
)

# pylint: disable=line-too-long
MOCK_PREDICTIONS_RESPONSE_FIRST_CALL = {
    "data": {
        "predictPredictions": [
            {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1698527100-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
                "user": {"id": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"},
                "stake": "0.050051425480971974",
                "payout": {"payout": "0", "trueValue": False, "predictedValue": True},
                "slot": {
                    "slot": 1698527100,
                    "predictContract": {
                        "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                        "token": {
                            "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                            "name": "ADA/USDT",
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
        ]
    }
}

MOCK_PREDICTIONS_RESPONSE_SECOND_CALL: Dict[str, dict] = {}

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
            {"id": "contract1", "secondsPerEpoch": 300},
            {"id": "contract2", "secondsPerEpoch": 600},
        ]
    }
}


@enforce_types
@patch("pdr_backend.util.subgraph_predictions.query_subgraph")
def test_fetch_filtered_predictions(mock_query_subgraph):
    mock_query_subgraph.side_effect = [
        MOCK_PREDICTIONS_RESPONSE_FIRST_CALL,
        MOCK_PREDICTIONS_RESPONSE_SECOND_CALL,
    ]
    predictions = fetch_filtered_predictions(
        start_ts=1622547000,
        end_ts=1622548800,
        filters=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        network="mainnet",
        filter_mode=FilterMode.PREDICTOOR,
    )

    assert len(predictions) == 1
    assert isinstance(predictions[0], Prediction)
    assert predictions[0].user == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"
    assert predictions[0].pair == "ADA/USDT"
    assert predictions[0].trueval is False
    assert predictions[0].prediction is True
    assert mock_query_subgraph.call_count == 2


@enforce_types
@patch(
    "pdr_backend.util.subgraph_predictions.query_subgraph",
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


@enforce_types
@patch(
    "pdr_backend.util.subgraph_predictions.query_subgraph",
    return_value=MOCK_CONTRACT_DETAILS_RESPONSE,
)
def test_fetch_contract_id_and_spe(
    mock_query_subgraph,
):  # pylint: disable=unused-argument
    contract_details = fetch_contract_id_and_spe(
        contract_addresses=["contract1", "contract2"], network="mainnet"
    )

    assert len(contract_details) == 2
    assert contract_details[0]["id"] == "contract1"
    assert contract_details[0]["seconds_per_epoch"] == 300
    assert contract_details[1]["id"] == "contract2"
    assert contract_details[1]["seconds_per_epoch"] == 600
    mock_query_subgraph.assert_called_once()
