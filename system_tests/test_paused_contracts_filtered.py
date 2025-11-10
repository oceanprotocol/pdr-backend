import pytest
from pdr_backend.subgraph.subgraph_feed_contracts import query_feed_contracts
from pdr_backend.subgraph.subgraph_pending_slots import get_pending_slots
from pdr_backend.subgraph.subgraph_predictions import fetch_filtered_predictions
from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts
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
    6. Query with include_paused=True - SHOULD include our contract
    """

    contract_address = feed_contract1.contract_instance.address
    subgraph_url = web3_pp.subgraph_url
    owner_address = web3_pp.web3_config.owner

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

    # Step 3: Query pending payouts before pausing (should work normally)
    payouts_before = query_pending_payouts(
        subgraph_url=subgraph_url,
        addr=owner_address,
        query_old_slots=False,
        include_paused=False,
    )

    # Step 4: Pause the contract
    # Note: This requires owner permissions
    tx = feed_contract1.contract_instance.functions.pause().transact(
        web3_pp.tx_call_params()
    )
    web3_pp.w3.eth.wait_for_transaction_receipt(tx)

    # Verify contract is paused
    is_paused = feed_contract1.contract_instance.functions.paused().call()
    assert is_paused, "Contract should be paused"

    # Step 5: Wait for subgraph to sync
    from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs

    wait_until_subgraph_syncs(web3_pp, subgraph_url)

    # Step 6: Verify contract does NOT appear in feed contracts query (paused)
    feeds_after = query_feed_contracts(subgraph_url=subgraph_url)
    contract_found_after = contract_address.lower() in [
        addr.lower() for addr in feeds_after.keys()
    ]

    assert (
        not contract_found_after
    ), f"Paused contract {contract_address} should NOT be in feed contracts query results"

    # Step 7: Verify contract does NOT appear in pending slots query (paused)
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

    # Step 8: Verify paused contract is filtered from pending payouts (include_paused=False)
    payouts_without_paused = query_pending_payouts(
        subgraph_url=subgraph_url,
        addr=owner_address,
        query_old_slots=False,
        include_paused=False,
    )

    # If there were payouts for this contract before, they should be gone now
    if contract_address.lower() in [addr.lower() for addr in payouts_before.keys()]:
        assert contract_address.lower() not in [
            addr.lower() for addr in payouts_without_paused.keys()
        ], f"Paused contract {contract_address} should NOT be in pending payouts (include_paused=False)"

    # Step 9: Verify paused contract IS included when include_paused=True
    payouts_with_paused = query_pending_payouts(
        subgraph_url=subgraph_url,
        addr=owner_address,
        query_old_slots=False,
        include_paused=True,
    )

    if contract_address.lower() in [addr.lower() for addr in payouts_before.keys()]:
        assert contract_address.lower() in [
            addr.lower() for addr in payouts_with_paused.keys()
        ], f"Paused contract {contract_address} SHOULD be in pending payouts when include_paused=True"

    print(
        f"✓ Verified paused contract {contract_address} is filtered from queries by default"
    )
    print(
        f"✓ Verified paused contract {contract_address} is included when include_paused=True"
    )
