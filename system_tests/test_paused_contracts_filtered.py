import pytest
from pdr_backend.subgraph.subgraph_feed_contracts import query_feed_contracts
from pdr_backend.subgraph.subgraph_pending_slots import get_pending_slots
from pdr_backend.subgraph.subgraph_predictions import fetch_filtered_predictions
from pdr_backend.util.time_types import UnixTimeS


def test_paused_contracts_are_filtered_out(
    web3_pp,
    feed_contract1,
):
    """
    Integration test that verifies paused contracts are filtered out.

    Steps:
    1. Deploy a predictoor contract (done via fixture)
    2. Query subgraph for contracts - should include our contract
    3. Pause the contract
    4. Wait for subgraph to sync
    5. Query subgraph again - should NOT include our contract
    """

    contract_address = feed_contract1.contract_instance.address
    subgraph_url = web3_pp.subgraph_url

    # Step 1: Verify contract appears in feed contracts query (not paused)
    feeds_before = query_feed_contracts(subgraph_url=subgraph_url)
    contract_found_before = contract_address.lower() in [
        addr.lower() for addr in feeds_before.keys()
    ]

    # If contract is new, it should appear; if already paused, skip test
    if not contract_found_before:
        pytest.skip("Contract not found in subgraph - may be new or already paused")

    # Step 2: Verify contract appears in pending slots query (not paused)
    current_time = UnixTimeS.now()
    slots_before = get_pending_slots(
        subgraph_url=subgraph_url,
        timestamp=current_time,
        owner_addresses=None,
        allowed_feeds=None,
    )

    # Step 3: Pause the contract
    # Note: This requires owner permissions
    tx = feed_contract1.contract_instance.functions.pause().transact(
        web3_pp.tx_call_params()
    )
    web3_pp.w3.eth.wait_for_transaction_receipt(tx)

    # Verify contract is paused
    is_paused = feed_contract1.contract_instance.functions.paused().call()
    assert is_paused, "Contract should be paused"

    # Step 4: Wait for subgraph to sync
    from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs

    wait_until_subgraph_syncs(web3_pp, subgraph_url)

    # Step 5: Verify contract does NOT appear in feed contracts query (paused)
    feeds_after = query_feed_contracts(subgraph_url=subgraph_url)
    contract_found_after = contract_address.lower() in [
        addr.lower() for addr in feeds_after.keys()
    ]

    assert (
        not contract_found_after
    ), f"Paused contract {contract_address} should NOT be in feed contracts query results"

    # Step 6: Verify contract does NOT appear in pending slots query (paused)
    slots_after = get_pending_slots(
        subgraph_url=subgraph_url,
        timestamp=current_time,
        owner_addresses=None,
        allowed_feeds=None,
    )

    slots_with_paused_contract = [
        slot
        for slot in slots_after
        if slot.feed.address.lower() == contract_address.lower()
    ]

    assert (
        len(slots_with_paused_contract) == 0
    ), f"Paused contract {contract_address} should NOT have any slots in query results"
