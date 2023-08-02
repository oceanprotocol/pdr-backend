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
if "OPF_DEPLOYER_PRIVATE_KEY" not in os.environ:
    print("Missing OPF_DEPLOYER_PRIVATE_KEY")
    exit(1)

deployer = br_accounts.add(os.getenv("OPF_DEPLOYER_PRIVATE_KEY"))
connect_to_network("development")
ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"
address_file = os.path.expanduser(ADDRESS_FILE)
print(f"Load contracts from address_file: {address_file}")
config = get_config_dict("development")
config["ADDRESS_FILE"] = address_file
ocean = Ocean(config)
OCEAN = ocean.OCEAN_token

# transfer ocean tokens to predictoor & trader
if "PREDICTOOR_PRIVATE_KEY" in os.environ:
    predictoor = br_accounts.add(os.getenv("PREDICTOOR_PRIVATE_KEY"))
    print("Sending Ocean to predictoor")
    OCEAN.transfer(predictoor.address, to_wei(2000.0), {"from": deployer})
if "PREDICTOOR2_PRIVATE_KEY" in os.environ:
    predictoor = br_accounts.add(os.getenv("PREDICTOOR2_PRIVATE_KEY"))
    print("Sending Ocean to predictoor2")
    OCEAN.transfer(predictoor.address, to_wei(2000.0), {"from": deployer})
if "PREDICTOOR3_PRIVATE_KEY" in os.environ:
    predictoor = br_accounts.add(os.getenv("PREDICTOOR3_PRIVATE_KEY"))
    print("Sending Ocean to predictoor3")
    OCEAN.transfer(predictoor.address, to_wei(2000.0), {"from": deployer})

if "TRADER_PRIVATE_KEY" in os.environ:
    trader = br_accounts.add(os.getenv("TRADER_PRIVATE_KEY"))
    print("Sending Ocean to trader")
    OCEAN.transfer(trader.address, to_wei(2000.0), {"from": deployer})

if "DFBUYER_PRIVATE_KEY" in os.environ:
    dfbuyer = br_accounts.add(os.getenv("DFBUYER_PRIVATE_KEY"))
    print("Sending Ocean to dfbuyer")
    OCEAN.transfer(dfbuyer.address, to_wei(10000.0), {"from": deployer})

if "PDR_WEBSOCKET_KEY" in os.environ:
    pdr_websocket_user = br_accounts.add(os.getenv("PDR_WEBSOCKET_KEY"))
    print("Sending Ocean to pdr_websocket_user")
    OCEAN.transfer(pdr_websocket_user.address, to_wei(10000.0), {"from": deployer})

if "PDR_MM_USER" in os.environ:
    pdr_mm_user = br_accounts.add(os.getenv("PDR_MM_USER"))
    print("Sending Ocean to pdr_mm_user")
    OCEAN.transfer(pdr_mm_user.address, to_wei(10000.0), {"from": deployer})

# create NFT
print("Creating NFT...")

S_PER_MIN = 60
S_PER_HOUR = 60 * 60
# for our ganache, have one epoch per minute (every 60 blocks)
s_per_block = 1  # depends on the chain
s_per_epoch = 1 * S_PER_MIN
s_per_subscription = 24 * S_PER_HOUR
min_predns_for_payout = 3  # ideally, 100+
stake_token = OCEAN
DT_price = 2

# 1st pair:  ETH-USDT on Kraken, 5m
data_nft = ocean.data_nft_factory.create(
    {"from": deployer}, "ETH-USDT-Kraken-5m", "ETH-USDT"
)
initial_list = data_nft.getTokensList()
print("Creating BTC-TUSD-Binance-5m...")
data_nft.createERC20(
    3,
    ["ETH-USDT", "ETH-USDT"],
    [
        deployer.address,
        deployer.address,
        deployer.address,
        OCEAN.address,
        OCEAN.address,
    ],
    [MAX_UINT256, 0, s_per_block, s_per_epoch, s_per_subscription, 30],
    [],
    {"from": deployer},
)
new_elements = [item for item in data_nft.getTokensList() if item not in initial_list]
assert len(new_elements) == 1, "new datatoken has no address"
DT = DatatokenBase.get_typed(config, new_elements[0])
print("Setting fixed price exchange")
DT.setup_exchange({"from": deployer}, to_wei(DT_price))
print("Setting key/values")
data_nft.set_data("pair", "ETH/USDT", {"from": deployer})
data_nft.set_data("base", "ETH", {"from": deployer})
data_nft.set_data("quote", "USDT", {"from": deployer})
data_nft.set_data("source", "kraken", {"from": deployer})
data_nft.set_data("timeframe", "5m", {"from": deployer})


# 2nd pair:  BTC-TUSD on Binance, 5m
data_nft = ocean.data_nft_factory.create(
    {"from": deployer}, "BTC-TUSD-Binance-5m", "BTC-TUSD"
)
initial_list = data_nft.getTokensList()
print("Creating BTC-TUSD-Binance-5m...")
data_nft.createERC20(
    3,
    ["BTC-TUSD", "BTC-TUSD"],
    [
        deployer.address,
        deployer.address,
        deployer.address,
        OCEAN.address,
        OCEAN.address,
    ],
    [MAX_UINT256, 0, s_per_block, s_per_epoch, s_per_subscription, 30],
    [],
    {"from": deployer},
)
new_elements = [item for item in data_nft.getTokensList() if item not in initial_list]
assert len(new_elements) == 1, "new datatoken has no address"
DT = DatatokenBase.get_typed(config, new_elements[0])
# print("Setting fixed price exchange")
DT.setup_exchange({"from": deployer}, to_wei(DT_price))
# print("Setting key/values")
data_nft.set_data("pair", "BTC/TUSD", {"from": deployer})
data_nft.set_data("base", "BTC", {"from": deployer})
data_nft.set_data("quote", "TUSD", {"from": deployer})
data_nft.set_data("source", "binance", {"from": deployer})
data_nft.set_data("timeframe", "5m", {"from": deployer})

# 3rd pair:  XRP-USDT on Binance, 5m
data_nft = ocean.data_nft_factory.create(
    {"from": deployer}, "XRP-USDT-Binance-5m", "XRP-USDT"
)
initial_list = data_nft.getTokensList()
print("Creating XRP-USDT-Binance-5m...")
data_nft.createERC20(
    3,
    ["XRP-USDT", "XRP-USDT"],
    [
        deployer.address,
        deployer.address,
        deployer.address,
        OCEAN.address,
        OCEAN.address,
    ],
    [MAX_UINT256, 0, s_per_block, s_per_epoch, s_per_subscription, 30],
    [],
    {"from": deployer},
)
new_elements = [item for item in data_nft.getTokensList() if item not in initial_list]
assert len(new_elements) == 1, "new datatoken has no address"
DT = DatatokenBase.get_typed(config, new_elements[0])
# print("Setting fixed price exchange")
DT.setup_exchange({"from": deployer}, to_wei(DT_price))
# print("Setting key/values")
data_nft.set_data("pair", "XRP/USDT", {"from": deployer})
data_nft.set_data("base", "XRP", {"from": deployer})
data_nft.set_data("quote", "USDT", {"from": deployer})
data_nft.set_data("source", "binance", {"from": deployer})
data_nft.set_data("timeframe", "5m", {"from": deployer})
print("Done")
