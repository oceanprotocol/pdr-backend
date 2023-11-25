import os
from typing import List, Union

from enforce_typing import enforce_types
from eth_account import Account

from pdr_backend.models.data_nft import DataNft
from pdr_backend.models.erc721_factory import ERC721Factory
from pdr_backend.models.token import Token
from pdr_backend.util.contract import get_address

MAX_UINT256 = 2**256 - 1


@enforce_types
def fund_dev_accounts(accounts_to_fund: List[tuple], owner: str, token: Token):
    for private_key_name, amount in accounts_to_fund:
        if private_key_name in os.environ:
            private_key = os.getenv(private_key_name)
            account = Account.from_key(  # pylint: disable=no-value-for-parameter
                private_key
            )
            print(
                f"Sending OCEAN to account defined by envvar {private_key_name}"
                f", with address {account.address}"
            )
            token.transfer(account.address, amount * 1e18, owner)


@enforce_types
def publish(
    s_per_epoch: int,
    s_per_subscription: int,
    base: str,
    quote: str,
    source: str,
    timeframe: str,
    trueval_submitter_addr: str,
    feeCollector_addr: str,
    rate: Union[int, float],
    cut: Union[int, float],
    web3_config,
):
    pair = base + "/" + quote
    trueval_timeout = 60 * 60 * 24 * 3
    owner = web3_config.owner
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    fre_address = get_address(web3_config.w3.eth.chain_id, "FixedPrice")
    factory = ERC721Factory(web3_config)

    feeCollector = web3_config.w3.to_checksum_address(feeCollector_addr)
    trueval_submiter = web3_config.w3.to_checksum_address(trueval_submitter_addr)

    rate_wei: int = web3_config.w3.to_wei(rate, "ether")
    cut_wei: int = web3_config.w3.to_wei(cut, "ether")

    nft_name: str = base + "-" + quote + "-" + source + "-" + timeframe
    nft_symbol: str = pair
    erc20_name: str = nft_symbol
    erc20_symbol: str = nft_symbol

    nft_data: tuple = (nft_name, nft_symbol, 1, "", True, owner)
    erc_data: tuple = (
        3,
        [erc20_name, erc20_symbol],
        [
            owner,
            owner,
            feeCollector,
            ocean_address,
            ocean_address,
        ],
        [MAX_UINT256, 0, s_per_epoch, s_per_subscription, trueval_timeout],
        [],
    )
    fre_data: tuple = (
        fre_address,
        [ocean_address, owner, feeCollector, owner],
        [18, 18, rate_wei, cut_wei, 1],
    )

    logs_nft, logs_erc = factory.createNftWithErc20WithFixedRate(
        nft_data, erc_data, fre_data
    )
    data_nft_address: str = logs_nft["newTokenAddress"]
    print(f"Deployed NFT: {data_nft_address}")

    data_nft = DataNft(web3_config, data_nft_address)
    tx = data_nft.set_data("pair", pair)
    print(f"Pair set to {pair} in {tx.hex()}")

    tx = data_nft.set_data("base", base)
    print(f"base set to {base} in {tx.hex()}")

    tx = data_nft.set_data("quote", quote)
    print(f"quote set to {quote} in {tx.hex()}")

    tx = data_nft.set_data("source", source)
    print(f"source set to {source} in {tx.hex()}")

    tx = data_nft.set_data("timeframe", timeframe)
    print(f"timeframe set to {timeframe} in {tx.hex()}")

    tx = data_nft.add_erc20_deployer(trueval_submiter)
    print(f"Erc20Deployer set to {trueval_submiter} in {tx.hex()}")

    return (nft_data, erc_data, fre_data, logs_nft, logs_erc)
