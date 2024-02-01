import copy
import json
import os
from pathlib import Path
from typing import Union

import artifacts
from enforce_typing import enforce_types


# TODO: I think some of these others functions warrant being moved to web3_pp.py
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
