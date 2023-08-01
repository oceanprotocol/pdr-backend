<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Deploy DT3

In this step, we deploy a datafeed following datatoken template 3.

We assume you've already
- (a) [installed pdr-backend](install.md),
- (b) [done local setup](setup-local.md) or [remote setup](setup-remote.md)

Since there is no easy way now to create a template3 datatoken, we will use ocean.py.

Steps in this flow:
1. Install ocean.py
2. Deploy DT3 via ocean.py

Let's go!

## 1. Install ocean.py

In a new console:
```console
# Install
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py
git checkout predictoor-with-barge
sudo apt-get update -y
sudo apt-get install -y
sudo apt-get install -y python3-dev gcc 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt

# Set envvars
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
export OPF_DEPLOYER_PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
export PREDICTOOR_PRIVATE_KEY="0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
export TRADER_PRIVATE_KEY="0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99"
```

## 2. Deploy DT3 via ocean.py

In the console, open Python console:
```console
python
```

Inside the Python console:
```python
import brownie
from brownie.network import accounts as br_accounts
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.ocean.util import from_wei, to_wei
from ocean_lib.example_config import get_config_dict
from ocean_lib.web3_internal.constants import ZERO_ADDRESS, MAX_UINT256
# add accounts
deployer = br_accounts.add(os.getenv("OPF_DEPLOYER_PRIVATE_KEY"))
predictoor = br_accounts.add(os.getenv("PREDICTOOR_PRIVATE_KEY"))
trader = br_accounts.add(os.getenv("TRADER_PRIVATE_KEY"))
connect_to_network("development")
ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"
address_file = os.path.expanduser(ADDRESS_FILE)
print(f"Load contracts from address_file: {address_file}")
config = get_config_dict("development")
config["ADDRESS_FILE"] = address_file
ocean = Ocean(config)
OCEAN = ocean.OCEAN_token

# transfer OCEAN to predictoor & trader
OCEAN.transfer(predictoor.address, to_wei(2000.0), {"from": deployer})
OCEAN.transfer(trader.address, to_wei(2000.0), {"from": deployer})

#create NFT
data_nft = ocean.data_nft_factory.create({"from": deployer}, "DN", "DN")

#settings for template 3
S_PER_MIN = 60
S_PER_HOUR = 60 * 60
# for our ganache, have one epoch per minute (every 60 blocks)
s_per_block = 1  # depends on the chain
s_per_epoch = 1 * S_PER_MIN
s_per_subscription = 24 * S_PER_HOUR
min_predns_for_payout = 3  # ideally, 100+
stake_token = OCEAN
DT_price = 2 # priced in OCEAN

#create template3
initial_list = data_nft.getTokensList()
data_nft.createERC20(
        3,
        ["ETH-USDT", "ETH-USDT"],
        [deployer.address, deployer.address, deployer.address, OCEAN.address, OCEAN.address],
        [MAX_UINT256, 0, s_per_block, s_per_epoch, s_per_subscription, 30],
        [],
        {"from": deployer},
    )
new_elements = [
        item for item in data_nft.getTokensList() if item not in initial_list
    ]
assert len(new_elements) == 1, "new datatoken has no address"
DT = DatatokenBase.get_typed(config, new_elements[0])
DT.setup_exchange({"from": deployer}, to_wei(DT_price))
print("Done")
```
