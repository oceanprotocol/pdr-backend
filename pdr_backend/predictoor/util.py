from typing import Dict, List, Tuple
from enforce_typing import enforce_types


@enforce_types
def find_shared_slots(
    pending_slots: Dict[str, List[int]],
    payout_batch_size: int,
) -> List[Tuple[List[str], List[int]]]:
    """
    This function is used to organize payout slots and contract addresses based on shared slots.

    @return
    List[Tuple[List[str], List[int]]]:
        A list of tuples where each tuple contains a list of
        addresses sharing the same slots and the slots they share.
    """
    slot_to_addresses: Dict[int, set] = {}

    # Collect all addresses for each slot
    for address, slots in pending_slots.items():
        for slot in slots:
            if slot not in slot_to_addresses:
                slot_to_addresses[slot] = set()
            slot_to_addresses[slot].add(address)

    # Build a dictionary to group addresses sharing the same slots
    address_combination_to_slots: Dict[tuple, List[int]] = {}
    for slot, addresses in slot_to_addresses.items():
        address_tuple = tuple(sorted(addresses))
        if address_tuple not in address_combination_to_slots:
            address_combination_to_slots[address_tuple] = []
        address_combination_to_slots[address_tuple].append(slot)

    # Split slots into batches based on payout_batch_size
    result: List[Tuple[List[str], List[int]]] = []
    for addresses, slots in address_combination_to_slots.items():  # type: ignore
        for i in range(0, len(slots), payout_batch_size):
            batch_slots = slots[i : i + payout_batch_size]
            result.append((list(addresses), batch_slots))

    return result


def to_checksum(w3, addrs: List[str]) -> List[str]:
    checksummed_addrs = [w3.to_checksum_address(addr) for addr in addrs]
    return checksummed_addrs
