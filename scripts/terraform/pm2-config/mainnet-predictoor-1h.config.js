module.exports = {
  apps : [{
    name   : "mainnet-predictoor-btc-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "BTC/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${BTC_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_btc",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-eth-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "ETH/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${ETH_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_eth",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-ada-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "ADA/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${ADA_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_ada",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-bnb-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "BNB/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${BNB_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_bnb",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-sol-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "SOL/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${SOL_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_sol",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-xrp-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "XRP/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${XRP_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_xrp",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-dot-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "DOT/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${DOT_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_dot",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-ltc-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "LTC/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${LTC_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_ltc",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-doge-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "DOGE/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${DOGE_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_doge",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  {
    name   : "mainnet-predictoor-trx-1h",
    script : "./pdr_backend/predictoor/main.py",
    args : "3",
    env: {
      PAIR_FILTER : "TRX/USDT",
      TIMEFRAME_FILTER : "1h",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "${TRX_1H_PK}",
      MODEL_SIGNALS : "close",
      MODEL_ST_TIMESTAMP : "2023-01-31",
      MODEL_SS : "LIN",
      MODEL_EXCHANGE_IDS : "binance",
      MODEL_CSVS : "csvs_trx",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  },
  ]
}