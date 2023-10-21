module.exports = {
  apps : [{
    name   : "mainnet-predictoor",
    script : "./pdr_backend/predictoor/main.py",
    args : "1",
    env: {
      PAIR_FILTER : "BTC/USDT",
      TIMEFRAME_FILTER : "5m",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "<YOUR_PRIVATE_KEY>",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://sapphire.oasis.io",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520",
      OWNER_ADDRS : "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703"
    }
  }]
}