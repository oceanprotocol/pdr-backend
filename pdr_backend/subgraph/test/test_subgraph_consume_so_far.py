from unittest.mock import patch

from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.subgraph.info725 import key_to_key725, value_to_value725
from pdr_backend.subgraph.subgraph_consume_so_far import get_consume_so_far_per_contract
from pdr_backend.util.time_types import UnixTimeSeconds

SAMPLE_CONTRACT_DATA = [
    {
        "id": "contract1",
        "token": {
            "id": "token1",
            "name": "ether",
            "symbol": "ETH",
            "orders": [
                {
                    "createdTimestamp": 1695288424,
                    "consumer": {"id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"},
                    "lastPriceValue": "2.4979184013322233",
                },
                {
                    "createdTimestamp": 1695288724,
                    "consumer": {"id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"},
                    "lastPriceValue": "2.4979184013322233",
                },
            ],
            "nft": {
                "owner": {"id": "0xowner1"},
                "nftData": [
                    {
                        "key": key_to_key725("pair"),
                        "value": value_to_value725("ETH/USDT"),
                    },
                    {
                        "key": key_to_key725("timeframe"),
                        "value": value_to_value725("5m"),
                    },
                    {
                        "key": key_to_key725("source"),
                        "value": value_to_value725("binance"),
                    },
                ],
            },
        },
        "secondsPerEpoch": 7,
        "secondsPerSubscription": 700,
        "truevalSubmitTimeout": 5,
    }
]


@enforce_types
def test_get_consume_so_far_per_contract():
    call_count = 0

    def mock_query_subgraph(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        nonlocal call_count
        slot_data = SAMPLE_CONTRACT_DATA

        if call_count > 0:
            slot_data[0]["token"]["orders"] = []

        call_count += 1
        return {"data": {"predictContracts": slot_data}}

    PATH = "pdr_backend.subgraph.subgraph_consume_so_far"
    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeSeconds(2000),
            contract_addresses=["contract1"],
        )

    assert consumes["contract1"] == approx(6, 0.001)


@enforce_types
def test_get_consume_so_far_per_contract_empty_data():
    def mock_query_subgraph(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        return {}

    PATH = "pdr_backend.subgraph.subgraph_consume_so_far"
    with patch(
        f"{PATH}.query_subgraph", mock_query_subgraph
    ):  # pylint:disable=unused-argument
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeSeconds(2000),
            contract_addresses=["contract1"],
        )

    assert consumes == {}

    def mock_query_subgraph_2(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        return {"data": {"predictContracts": []}}

    with patch(f"{PATH}.query_subgraph", mock_query_subgraph_2):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeSeconds(2000),
            contract_addresses=["contract1"],
        )

    assert consumes == {}

    def mock_query_subgraph_3(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        return {"data": {"predictContracts": [{"id": "contract2"}]}}

    with patch(f"{PATH}.query_subgraph", mock_query_subgraph_3):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeSeconds(2000),
            contract_addresses=["contract1"],
        )

    assert consumes == {}
