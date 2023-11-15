import json
import os
from pathlib import Path
from typing import Union

import addresses
import artifacts
from enforce_typing import enforce_types


@enforce_types
def get_address(chain_id: int, contract_name: str):
    network = get_addresses(chain_id)
    if not network:
        raise ValueError(f"Cannot figure out {contract_name} address")
    address = network.get(contract_name)
    return address


@enforce_types
def get_addresses(chain_id: int):
    address_filename = os.getenv("ADDRESS_FILE")
    path = None
    if address_filename:
        address_filename = os.path.expanduser(address_filename)
        path = Path(address_filename)
    else:
        path = Path(str(os.path.dirname(addresses.__file__)) + "/address.json")

    if not path.exists():
        raise TypeError(f"Cannot find address.json file at {path}")

    with open(path) as f:
        data = json.load(f)
    for name in data:
        network = data[name]
        if network["chainId"] == chain_id:
            return network
    return None


@enforce_types
def get_contract_abi(contract_name):
    """Returns the abi dict for a contract name."""
    path = get_contract_filename(contract_name)

    if not path.exists():
        raise TypeError("Contract name does not exist in artifacts.")

    with open(path) as f:
        data = json.load(f)
        return data["abi"]


@enforce_types
def get_contract_filename(contract_name: str):
    """Returns filename for a contract name."""
    contract_basename = f"{contract_name}.json"

    # first, try to find locally
    address_filename = os.getenv("ADDRESS_FILE")
    path: Union[None, str, Path] = None
    if address_filename:
        address_filename = os.path.expanduser(address_filename)
        address_dir = os.path.dirname(address_filename)
        root_dir = os.path.join(address_dir, "..")
        paths = list(Path(root_dir).rglob(contract_basename))
        if paths:
            assert len(paths) == 1, "had duplicates for {contract_basename}"
            path = paths[0]
            path = Path(path).expanduser().resolve()
            assert (
                path.exists()
            ), f"Found path = '{path}' via glob, yet path.exists() is False"
            return path

    # didn't find locally, so use use artifacts lib
    path = os.path.join(os.path.dirname(artifacts.__file__), "", contract_basename)
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise TypeError(f"Contract '{contract_name}' not found in artifacts.")
    return path
