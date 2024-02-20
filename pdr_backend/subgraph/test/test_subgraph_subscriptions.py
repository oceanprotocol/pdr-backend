from typing import Dict
from unittest.mock import patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_subscriptions import (
    Subscription,
    fetch_filtered_subscriptions,
)
from pdr_backend.util.time_types import UnixTimeSeconds

SAMPLE_PREDICTION = Subscription(
    # pylint: disable=line-too-long
    ID="0x18f54cc21b7a2fdd011bea06bba7801b280e3151-0x00d1e4950e0de743fe88956f02f44b16d22a1827f8c29ff561b69716dbcc2677-14",
    pair="ADA/USDT",
    timeframe="5m",
    source="binance",
    timestamp=UnixTimeSeconds(1701129777),
    tx_id="0x00d1e4950e0de743fe88956f02f44b16d22a1827f8c29ff561b69716dbcc2677",
    last_price_value=float("2.4979184013322233") * 1.201,
    user="0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
)

# pylint: disable=line-too-long
MOCK_SUBSCRIPTIONS_RESPONSE_FIRST_CALL = {
    "data": {
        "predictSubscriptions": [
            {
                "id": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-0x00d1e4950e0de743fe88956f02f44b16d22a1827f8c29ff561b69716dbcc2677-14",
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
                        "lastPriceValue": "2.4979184013322233",
                    },
                    "secondsPerSubscription": "86400",
                    "secondsPerEpoch": "300",
                },
                "user": {"id": "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d"},
                "expireTime": "1701216000",
                "eventIndex": 14,
                "block": 1342747,
                "timestamp": 1701129777,
                "txId": "0x00d1e4950e0de743fe88956f02f44b16d22a1827f8c29ff561b69716dbcc2677",
            }
        ]
    }
}

MOCK_SUBSCRIPTIONS_RESPONSE_SECOND_CALL: Dict[str, dict] = {}


@enforce_types
@patch("pdr_backend.subgraph.subgraph_subscriptions.query_subgraph")
def test_fetch_filtered_subscriptions(mock_query_subgraph):
    mock_query_subgraph.side_effect = [
        MOCK_SUBSCRIPTIONS_RESPONSE_FIRST_CALL,
        MOCK_SUBSCRIPTIONS_RESPONSE_SECOND_CALL,
    ]
    subscriptions = fetch_filtered_subscriptions(
        start_ts=UnixTimeSeconds(1701129700),
        end_ts=UnixTimeSeconds(1701129800),
        contracts=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        network="mainnet",
    )

    assert len(subscriptions) == 1
    assert isinstance(subscriptions[0], Subscription)
    assert subscriptions[0].user == "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d"
    assert subscriptions[0].pair == "ADA/USDT"
    assert mock_query_subgraph.call_count == 1


@enforce_types
def test_fetch_filtered_subscriptions_no_data():
    # network not supported
    with pytest.raises(Exception):
        fetch_filtered_subscriptions(
            start_ts=UnixTimeSeconds(1701129700),
            end_ts=UnixTimeSeconds(1701129800),
            contracts=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="xyz",
        )

    with patch(
        "pdr_backend.subgraph.subgraph_subscriptions.query_subgraph"
    ) as mock_query_subgraph:
        mock_query_subgraph.return_value = {"data": {}}
        subscriptions = fetch_filtered_subscriptions(
            start_ts=UnixTimeSeconds(1701129700),
            end_ts=UnixTimeSeconds(1701129800),
            contracts=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="mainnet",
        )
    assert len(subscriptions) == 0

    with patch(
        "pdr_backend.subgraph.subgraph_subscriptions.query_subgraph"
    ) as mock_query_subgraph:
        mock_query_subgraph.return_value = {"data": {"predictPredictions": []}}
        subscriptions = fetch_filtered_subscriptions(
            start_ts=UnixTimeSeconds(1701129700),
            end_ts=UnixTimeSeconds(1701129800),
            contracts=["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
            network="mainnet",
        )

    assert len(subscriptions) == 0
