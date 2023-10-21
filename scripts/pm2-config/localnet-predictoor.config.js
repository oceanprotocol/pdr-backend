module.exports = {
  apps : [{
    name   : "localnet-predictoor",
    script : "./pdr_backend/predictoor/main.py",
    args : "1",
    env: {
      ADDRESS_FILE : "${HOME}/.ocean/ocean-contracts/artifacts/address.json",
      RPC_URL : "http://127.0.0.1:8545",
      SUBGRAPH_URL : "http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph",
      PRIVATE_KEY : "0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58",
    }
  }]
}
