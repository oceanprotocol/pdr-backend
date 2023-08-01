# pdr-backend

## 0. Intro

Predictoor backend repo.

- This repo merges prior repos: pdr-utils + pdr-trueval + pdr-predictoor + pdr-trader + pdr-dfbuyer.
  - Each has its own sub-directory
  - Each has its own unit tests
- Plus system-level tests
- Plus system-level READMEs

(Once it's working, we no longer need any of the above pdr-* repos)

## 1. Usage/Dev: Frontend Devs

### 1.1 Frontend Devs: Quickstart

For those developing predictoor.ai or other frontends. Uses barge locally. Backend components don't change.

**[Frontend-dev](READMEs/frontend-dev.md)**

# 2. Usage/Dev: Backend Devs, Predictoors, Traders

### 2.1 Backend Devs: Quickstart

For those who want to change backend components (predictoor, trader, ..)

- **[Backend-dev-local](READMEs/backend-dev-local.md)** -- Local components
- **[Backend-dev-remote](READMEs/backend-dev-remote.md)** -- Remote components

Then, observe:
- Relax & watch as pdr-predictoor is submiting random predictions , pdr-trueval submits random true_vals for each epoch and pdr-trader signals trades.
- You can query [subgraph](http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql) and see [this populated data PR](https://github.com/oceanprotocol/ocean-subgraph/pull/678) here for entities 

### 2.2 Backend Devs: Customize

Ways to customize
- Customize [pdr-trueval](https://github.com/oceanprotocol/pdr-trueval) to submit real data, not random.
- Customize [pdr-predictoor](https://github.com/oceanprotocol/pdr-predictoor) to submit real predictions, not random.
- Customize [pdr-trader](https://github.com/oceanprotocol/pdr-trader) to actually trade.

### 2.3 Backend Devs: Testing

In console:
```console
#run a single test
pytest ocean_lib/models/test/test_data_nft_factory.py::test_start_multiple_order

#run all tests in a file
pytest ocean_lib/models/test/test_data_nft_factory.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

### 2.4 Backend Devs: Release Process

(FIXME)

## Appendix

### Appendix: Useful Links

To docker images
- https://hub.docker.com/r/oceanprotocol/ocean-contracts
- etc

PR for old vs new predictoor in barge:
- https://github.com/oceanprotocol/barge/blob/2bf56ed49abc478d3c5555aaacf7443b0e56a7ed/start_ocean.sh

### Appendix: On Private Keys

The READMEs above use these private keys from barge:
- OPF_DEPLOYER_PRIVATE_KEY:  `0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58`  - contracts owner, ocean token owner
- PREDICTOOR_PRIVATE_KEY: `0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209`  - predictoor
- TRADER_PRIVATE_KEY: `0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99`  - trader