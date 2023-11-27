import copy
import json
import os
from pathlib import Path
from typing import Union

import addresses
import artifacts
from enforce_typing import enforce_types


@enforce_types
def get_address(web3_pp, contract_name: str):
    network = get_addresses(web3_pp)
    if not network:
        raise ValueError(f"Cannot figure out {contract_name} address")
    address = network.get(contract_name)
    return address


@enforce_types
def get_addresses(web3_pp):
    address_file = web3_pp.address_file

    path = None
    if address_file:
        address_file = os.path.expanduser(address_file)
        path = Path(address_file)
    else:
        path = Path(str(os.path.dirname(addresses.__file__)) + "/address.json")

    if not path.exists():
        raise TypeError(f"Cannot find address.json file at {path}")

    with open(path) as f:
        d = json.load(f)

    d = _saphire_to_sapphire(d)

    if "barge" in web3_pp.network:  # eg "barge-pytest"
        return d["development"]
    if web3_pp.network in d:  # eg "development", "oasis_sapphire"
        return d[web3_pp.network]
    return None


@enforce_types
def _saphire_to_sapphire(d: dict) -> dict:
    """Fix spelling error coming from address.json"""
    d2 = copy.deepcopy(d)
    names = list(d.keys())  # eg ["mumbai", "oasis_saphire"]
    for name in names:
        if "saphire" in name:
            fixed_name = name.replace("saphire", "sapphire")
            d2[fixed_name] = d[name]
    return d2


@enforce_types
def get_contract_abi(contract_name: str, address_file: Union[str, None]):
    """Returns the abi dict for a contract name."""
    path = get_contract_filename(contract_name, address_file)

    if not path.exists():
        raise TypeError("Contract name does not exist in artifacts.")

    with open(path) as f:
        data = json.load(f)
        return data["abi"]


@enforce_types
def get_contract_filename(contract_name: str, address_file: Union[str, None]):
    """Returns filename for a contract name."""
    contract_basename = f"{contract_name}.json"

    # first, try to find locally
    path: Union[None, str, Path] = None
    if address_file:
        address_file = os.path.expanduser(address_file)
        address_dir = os.path.dirname(address_file)
        root_dir = os.path.join(address_dir, "..")
        paths = list(Path(root_dir).rglob(contract_basename))
        if paths:
            assert len(paths) == 1, f"had duplicates for {contract_basename}"
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
