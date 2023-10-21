module.exports = {
  apps : [{
    name   : "testnet-trader",
    script : "./pdr_backend/trader/approach1/main.py",
    env: {
      PAIR_FILTER : "BTC/USDT",
      TIMEFRAME_FILTER : "5m",
      SOURCE_FILTER : "binance",
      PRIVATE_KEY : "<YOUR_PRIVATE_KEY>",
      EXCHANGE_API_KEY : "<EXCHANGE_API_KEY>",
      EXCHANGE_SECRET_KEY : "<EXCHANGE_SECRET_KEY>",
      POSITION_SIZE_USD : "<POSITION_SIZE_USD>",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "https://testnet.sapphire.oasis.dev",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x973e69303259B0c2543a38665122b773D28405fB",
      OWNER_ADDRS : "0xe02a421dfc549336d47efee85699bd0a3da7d6ff"
    }
  }]
}