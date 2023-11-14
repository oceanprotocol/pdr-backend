ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MAX_UINT = 2**256 - 1

SAPPHIRE_TESTNET_RPC = "https://testnet.sapphire.oasis.dev"
SAPPHIRE_TESTNET_CHAINID = 23295
SAPPHIRE_MAINNET_RPC = "https://sapphire.oasis.io"
SAPPHIRE_MAINNET_CHAINID = 23294

S_PER_MIN = 60
S_PER_DAY = 86400

SUBGRAPH_MAX_TRIES = 5
WEB3_MAX_TRIES = 5

CAND_USDCOINS = ["USDT", "USDC", "DAI", "RAI"]  # add more if needed
CAND_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
CAND_SIGNALS = ["open", "high", "low", "close", "volume"]
CHAR_TO_SIGNAL =  {"o" : "open", "h" : "high", "l" : "low",
                   "c" : "close", "v" : "volume"}
