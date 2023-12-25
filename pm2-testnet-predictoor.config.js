module.exports = {
  apps : [{
    name   : "pm2-testnet-predictoor-btc-5m",
    script : "./pdr predictoor 3 my_ppss_btc_5m.yaml sapphire-testnet",
    env: {
      PRIVATE_KEY : "0xc882cea54b6ca367ab7ae06bdb727004021034effa02214609974526685097d1",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      PAIR_FILTER : "BTC/USDT",
      TIMEFRAME_FILTER : "5m",
      SOURCE_FILTER : "binance",
      RPC_URL : "https://testnet.sapphire.oasis.dev",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x973e69303259B0c2543a38665122b773D28405fB",
      OWNER_ADDRS : "0xe02a421dfc549336d47efee85699bd0a3da7d6ff"
    }
  },
  {
    name   : "pm2-testnet-predictoor-eth-5m",
    script : "./pdr predictoor 3 my_ppss_eth_5m.yaml sapphire-testnet",
    env: {
      PRIVATE_KEY : "0xd0239747d5ba4b9bd9e9fd229b478710fd3fb8b2dc9215ab8b681136491d2b1e",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      PAIR_FILTER : "ETH/USDT",
      TIMEFRAME_FILTER : "5m",
      SOURCE_FILTER : "binance",
      RPC_URL : "https://testnet.sapphire.oasis.dev",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x973e69303259B0c2543a38665122b773D28405fB",
      OWNER_ADDRS : "0xe02a421dfc549336d47efee85699bd0a3da7d6ff"
    }
  },
  {
    name   : "pm2-testnet-predictoor-ada-5m",
    script : "./pdr predictoor 3 my_ppss_ada_5m.yaml sapphire-testnet",
    env: {
      PRIVATE_KEY : "0x922ee55b3aceee62d29840b80bfb7caad5dbbca6864a3d5d5d6f58ff1877fcd4",
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      PAIR_FILTER : "ADA/USDT",
      TIMEFRAME_FILTER : "5m",
      SOURCE_FILTER : "binance",
      RPC_URL : "https://testnet.sapphire.oasis.dev",
      SUBGRAPH_URL : "https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
      STAKE_TOKEN : "0x973e69303259B0c2543a38665122b773D28405fB",
      OWNER_ADDRS : "0xe02a421dfc549336d47efee85699bd0a3da7d6ff"
    }
  }]
}
