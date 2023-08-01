# Usage: For Frontend Devs

For those developing predictoor.ai or other frontends. Uses barge locally. Backend components don't change.
- aka "Full Barge Approach"
- This flow runs everything in barge (including pdr-trader, pdr-trueval, pdr-predictoor and pdr-publisher).
- Useful for UI developers, when they don't care about data, as long it's there (some random values are enough)

### Steps

Open new terminal, call it "barge". In it:
```console
# Install
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
git clone https://github.com/oceanprotocol/barge.git
cd barge
git checkout predictoor

# (These are stable versions for GUI dev. We'll switch instructions to "use latest versions" once backend stabilizes again)
docker pull oceanprotocol/ocean-contracts:predictoor2
docker pull oceanprotocol/subgraph:predictoor
docker pull oceanprotocol/pdr-trader:v0.0.1
docker pull oceanprotocol/pdr-trueval:v0.0.1
docker pull oceanprotocol/pdr-predictoor:v0.0.1
docker pull oceanprotocol/pdr-publisher:v0.0.1
docker pull oceanprotocol/pdr-dfbuyer:v0.0.1

# Run
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

This will start barge with a custom version of ganache (auto-mine a block every 12 sec), contracts (predictoor), subgraph (predictoor)
- WARNING!! Barge will start more slowly. Deploying contracts takes a couple of minutes.
- Watch the output to know when to proceed further or check if file "/ocean-subgraph/ready" exists.

After barge is deployed, pdr* will wait for two epochs to pass, before consuming values. Wait for that first :)
