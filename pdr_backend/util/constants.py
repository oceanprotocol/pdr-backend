#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MAX_UINT = 2**256 - 1

DEVELOPMENT_CHAINID = 8996

SAPPHIRE_TESTNET_RPC = "https://testnet.sapphire.oasis.dev"
SAPPHIRE_TESTNET_CHAINID = 23295

SAPPHIRE_MAINNET_RPC = "https://sapphire.oasis.io"
SAPPHIRE_MAINNET_CHAINID = 23294

OCEAN_TOKEN_ADDRS = {
    SAPPHIRE_MAINNET_CHAINID: "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
    SAPPHIRE_TESTNET_CHAINID: "0x973e69303259B0c2543a38665122b773D28405fB",
}

S_PER_MIN = 60
S_PER_DAY = 86400
S_PER_WEEK = S_PER_DAY * 7

SUBGRAPH_MAX_TRIES = 5
WEB3_MAX_TRIES = 5

CAND_USDCOINS = ["USDT", "USDC", "DAI", "RAI", "USD"]  # add more if needed
CAND_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
CHAR_TO_SIGNAL = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}

# font size for plots
FONTSIZE = 9
