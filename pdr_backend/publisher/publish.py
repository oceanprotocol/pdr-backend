import os

from eth_account import Account

from pdr_backend.utils.contract import (
    DataNft,
    ERC721Factory,
    get_address,
)

MAX_UINT256 = 2**256 - 1


def fund_dev_accounts(accounts_to_fund, owner, token):
    for env_key, amount in accounts_to_fund:
        if env_key in os.environ:
            account = Account.from_key(os.getenv(env_key))
            print(
                f"Sending OCEAN to account defined by envvar key {env_key}, with address {account.address}"
            )
            token.transfer(account.address, amount * 1e18, owner)


def publish(
    s_per_epoch,
    s_per_subscription,
    base,
    quote,
    source,
    timeframe,
    trueval_submitter_addr,
    feeCollector_addr,
    rate,
    cut,
    web3_config,
):
    pair = base + "/" + quote
    trueval_timeout = 4 * 12 * s_per_epoch
    owner = web3_config.owner
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    fre_address = get_address(web3_config.w3.eth.chain_id, "FixedPrice")
    factory = ERC721Factory(web3_config)

    feeCollector = web3_config.w3.to_checksum_address(feeCollector_addr)
    trueval_submiter = web3_config.w3.to_checksum_address(trueval_submitter_addr)

    rate = web3_config.w3.to_wei(rate, "ether")
    cut = web3_config.w3.to_wei(cut, "ether")

    nft_name = base + "-" + quote + "-" + source + "-" + timeframe
    nft_symbol = pair
    erc20_name = nft_symbol
    erc20_symbol = nft_symbol

    nft_data = (nft_name, nft_symbol, 1, "", True, owner)
    erc_data = (
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
    fre_data = (
        fre_address,
        [ocean_address, owner, feeCollector, owner],
        [18, 18, rate, cut, 1],
    )

    data_nft_address = factory.createNftWithErc20WithFixedRate(
        nft_data, erc_data, fre_data
    )
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
