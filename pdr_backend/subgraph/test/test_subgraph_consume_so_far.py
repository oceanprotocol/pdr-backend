#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.subgraph.subgraph_consume_so_far import get_consume_so_far_per_contract
from pdr_backend.util.time_types import UnixTimeS


SAMPLE_CONTRACT_DATA = [
    {
        "user": {"id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"},
        "predictContract": {"id": "contract1"},
    },
    {
        "user": {"id": "0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a"},
        "predictContract": {"id": "contract1"},
    },
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
            slot_data = []

        call_count += 1
        return {"data": {"predictSubscriptions": slot_data}}

    PATH = "pdr_backend.subgraph.subgraph_consume_so_far"
    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeS(2000),
            contract_addresses=["contract1"],
        )

    assert consumes["contract1"] == approx(6, 0.001)


@enforce_types
def test_get_consume_so_far_per_contract_empty_data():

    def mock_query_subgraph(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        return {"data": {"predictSubscriptions": [{"id": "contract2"}]}}

    with patch(f"{PATH}.query_subgraph", mock_query_subgraph):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeS(2000),
            contract_addresses=["contract1"],
        )

    assert consumes == {}

    def mock_query_subgraph_2(
        subgraph_url, query, tries, timeout
    ):  # pylint:disable=unused-argument
        return {"data": {"predictSubscriptions": []}}

    with patch(f"{PATH}.query_subgraph", mock_query_subgraph_2):
        consumes = get_consume_so_far_per_contract(
            subgraph_url="foo",
            user_address="0xff8dcdfc0a76e031c72039b7b1cd698f8da81a0a",
            since_timestamp=UnixTimeS(2000),
            contract_addresses=["contract1"],
        )

    assert consumes == {}
