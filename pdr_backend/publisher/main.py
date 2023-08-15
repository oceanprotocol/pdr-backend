import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.ocean.util import to_wei
from ocean_lib.example_config import get_config_dict
from ocean_lib.web3_internal.constants import ZERO_ADDRESS, MAX_UINT256
from pdr_backend.publisher.publish import publish

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


publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="ETH",
    quote="USDT",
    source="kraken",
    timeframe="5m",
    trueval_submitter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",  # barge trueval submitter address
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)

publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="BTC",
    quote="TUSD",
    source="binance",
    timeframe="5m",
    trueval_submitter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)

publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="XRP",
    quote="USDT",
    source="binance",
    timeframe="5m",
    trueval_submitter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)
