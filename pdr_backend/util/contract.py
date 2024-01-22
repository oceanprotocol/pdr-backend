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
    """
    Returns address for this contract
    in web3_pp.address_file, in web3_pp.network
    """
    network = get_addresses(web3_pp)
    if not network:
        raise ValueError(f'Cannot find network "{web3_pp.network}" in addresses.json')

    address = network.get(contract_name)
    if not address:
        error = (
            f'Cannot find contract "{contract_name}" in address.json '
            f'for network "{web3_pp.network}"'
        )
        raise ValueError(error)

    return address


@enforce_types
def get_addresses(web3_pp) -> Union[dict, None]:
    """
    Returns addresses in web3_pp.address_file, in web3_pp.network
    """
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

    d = _condition_sapphire_keys(d)

    if "barge" in web3_pp.network:  # eg "barge-pytest"
        return d["development"]

    if web3_pp.network in d:  # eg "development", "oasis_sapphire"
        return d[web3_pp.network]

    return None


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


@enforce_types
def _condition_sapphire_keys(d: dict) -> dict:
    """
    For each sapphire-related key seen from address.json,
    transform it to something friendly to pdr-backend (and named better)
    """
    d2 = copy.deepcopy(d)
    names = list(d.keys())  # eg ["mumbai", "oasis_saphire"]
    for name in names:
        if name == "oasis_saphire_testnet":
            d2["sapphire-testnet"] = d[name]
        elif name == "oasis_saphire":
            d2["sapphire-mainnet"] = d[name]
    return d2
