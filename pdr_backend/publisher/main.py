from pdr_backend.models.token import Token
from pdr_backend.publisher.publish import publish, fund_dev_accounts
from pdr_backend.util.contract import get_address
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.web3_config import Web3Config


def main():
    rpc_url = getenv_or_exit("RPC_URL")
    private_key = getenv_or_exit("PRIVATE_KEY")

    # pairs to deploy on testnet and mainnet
    pair_list = ["BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "LTC", "TRX", "DOT"]

    # token price
    rate = 3 / (1 + 0.2 + 0.001)

    web3_config = Web3Config(rpc_url, private_key)

    if web3_config.w3.eth.chain_id == 8996:
        ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
        OCEAN = Token(web3_config, ocean_address)
        accounts_to_fund = [
            #    account_key_env,   OCEAN_to_send
            ("PREDICTOOR_PRIVATE_KEY", 2000.0),
            ("PREDICTOOR2_PRIVATE_KEY", 2000.0),
            ("PREDICTOOR3_PRIVATE_KEY", 2000.0),
            ("TRADER_PRIVATE_KEY", 2000.0),
            ("DFBUYER_PRIVATE_KEY", 10000.0),
            ("PDR_WEBSOCKET_KEY", 10000.0),
            ("PDR_MM_USER", 10000.0),
        ]

        fund_dev_accounts(accounts_to_fund, web3_config.owner, OCEAN)

        publish(
            s_per_epoch=300,
            s_per_subscription=60 * 60 * 24,
            base="ETH",
            quote="USDT",
            source="binance",
            timeframe="5m",
            trueval_submitter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",  # on arge
            feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
            rate=rate,
            cut=0.2,
            web3_config=web3_config,
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
            rate=rate,
            cut=0.2,
            web3_config=web3_config,
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
            rate=rate,
            cut=0.2,
            web3_config=web3_config,
        )

    if web3_config.w3.eth.chain_id == 23295:
        helper_contract = get_address(web3_config.w3.eth.chain_id, "PredictoorHelper")
        fee_collector = getenv_or_exit("FEE_COLLECTOR")
        for pair in pair_list:
            publish(
                s_per_epoch=300,
                s_per_subscription=60 * 60 * 24,
                base=pair,
                quote="USDT",
                source="binance",
                timeframe="5m",
                trueval_submitter_addr=helper_contract,
                feeCollector_addr=fee_collector,
                rate=rate,
                cut=0.2,
                web3_config=web3_config,
            )
            publish(
                s_per_epoch=3600,
                s_per_subscription=60 * 60 * 24,
                base=pair,
                quote="USDT",
                source="binance",
                timeframe="1h",
                trueval_submitter_addr=helper_contract,
                feeCollector_addr=fee_collector,
                rate=rate,
                cut=0.2,
                web3_config=web3_config,
            )

    if web3_config.w3.eth.chain_id == 23294:
        helper_contract = get_address(web3_config.w3.eth.chain_id, "PredictoorHelper")
        fee_collector = getenv_or_exit("FEE_COLLECTOR")
        for pair in pair_list:
            publish(
                s_per_epoch=300,
                s_per_subscription=60 * 60 * 24,
                base=pair,
                quote="USDT",
                source="binance",
                timeframe="5m",
                trueval_submitter_addr=helper_contract,
                feeCollector_addr=fee_collector,
                rate=rate,
                cut=0.2,
                web3_config=web3_config,
            )
            publish(
                s_per_epoch=3600,
                s_per_subscription=60 * 60 * 24,
                base=pair,
                quote="USDT",
                source="binance",
                timeframe="1h",
                trueval_submitter_addr=helper_contract,
                feeCollector_addr=fee_collector,
                rate=rate,
                cut=0.2,
                web3_config=web3_config,
            )


if __name__ == "__main__":
    main()
