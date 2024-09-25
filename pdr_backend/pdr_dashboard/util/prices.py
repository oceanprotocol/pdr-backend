import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from enforce_typing import enforce_types
from web3 import Web3

from pdr_backend.exchange.fetch_ohlcv import fetch_ohlcv
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.currency_types import Eth, Wei
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("predictoor_dashboard_utils")


@enforce_types
def calculate_tx_gas_fee_cost_in_OCEAN(
    web3_pp: Web3PP, feed_contract_addr: str, prices: Optional[Dict[str, float]]
) -> float:
    if not prices:
        return 0.0

    web3 = Web3(Web3.HTTPProvider(web3_pp.rpc_url))

    # generic params
    predicted_value = True
    stake_amt_wei = Eth(10).to_wei().amt_wei
    prediction_ts = Eth(1721723066).to_wei().amt_wei

    # gas price
    gas_price = web3.eth.gas_price

    # gas amount
    contract = web3.eth.contract(
        address=web3.to_checksum_address(feed_contract_addr),
        abi=web3_pp.get_contract_abi("ERC20Template3"),
    )

    gas_estimate_prediction = contract.functions["submitPredval"](
        # type: ignore[misc]
        predicted_value,
        stake_amt_wei,
        prediction_ts,
    ).estimate_gas({"from": "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"})

    # cals tx fee cost
    tx_fee_rose_prediction = (
        Wei(gas_estimate_prediction * gas_price).to_eth().amt_eth / 10
    )

    tx_fee_price_usdt_prediction = tx_fee_rose_prediction * prices["ROSE"]
    tx_fee_price_ocean_prediction = tx_fee_price_usdt_prediction / prices["OCEAN"]

    return tx_fee_price_ocean_prediction


@enforce_types
def _get_from_exchange(exchange: str, current_date_ms: UnixTimeMs) -> Tuple:
    rose_usdt = fetch_ohlcv(exchange, "ROSE/USDT", "5m", current_date_ms, 1)
    fet_usdt = fetch_ohlcv(exchange, "FET/USDT", "5m", current_date_ms, 1)

    return rose_usdt, fet_usdt


def fetch_token_prices() -> Optional[Dict[str, float]]:
    current_date_ms = UnixTimeMs.from_dt(datetime.now()) - 300000
    rose_usdt, fet_usdt = _get_from_exchange("binance", current_date_ms)

    if rose_usdt and fet_usdt:
        return {"ROSE": rose_usdt[0][1], "OCEAN": fet_usdt[0][1] * 0.433226}

    rose_usdt, fet_usdt = _get_from_exchange("binanceus", current_date_ms)

    if rose_usdt and fet_usdt:
        return {"ROSE": rose_usdt[0][1], "OCEAN": fet_usdt[0][1] * 0.433226}

    return None
