import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.ocean.util import to_wei
from ocean_lib.example_config import get_config_dict
from ocean_lib.web3_internal.constants import ZERO_ADDRESS, MAX_UINT256
from pdr_backend.publisher.publish import publish, fund_dev_accounts

# add accounts
if "OPF_DEPLOYER_PRIVATE_KEY" not in os.environ:
    print("Missing OPF_DEPLOYER_PRIVATE_KEY")
    exit(1)

deployer = Account.from_key(os.getenv("OPF_DEPLOYER_PRIVATE_KEY"))
connect_to_network("development")
ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"
address_file = os.path.expanduser(ADDRESS_FILE)
print(f"Load contracts from address_file: {address_file}")
config = get_config_dict("development")
config["ADDRESS_FILE"] = address_file
ocean = Ocean(config)
OCEAN = ocean.OCEAN_token

accounts_to_fund = [
    ("PREDICTOOR_PRIVATE_KEY", 2000.0),
    ("PREDICTOOR2_PRIVATE_KEY", 2000.0),
    ("PREDICTOOR3_PRIVATE_KEY", 2000.0),
    ("TRADER_PRIVATE_KEY", 2000.0),
    ("DFBUYER_PRIVATE_KEY", 10000.0),
    ("PDR_WEBSOCKET_KEY", 10000.0),
    ("PDR_MM_USER", 10000.0),
]

fund_dev_accounts(accounts_to_fund, OCEAN)

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
