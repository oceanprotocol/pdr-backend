# pdr-system

Predictoor backend repo.

- This repo merges prior repos: pdr-utils + pdr-trueval + pdr-predictoor + pdr-trader + pdr-dfbuyer.
  - Each has its own sub-directory
  - Each has its own unit tests
- Plus system-level tests
- Plus system-level READMEs

(Once it's working, we no longer need any of the above pdr-* repos)

# Usage

### Usage: For Frontend Devs

For those developing predictoor.ai or other frontends. Uses barge locally. Backend components don't change.

- [Frontend-dev](READMEs/frontend-dev.md)

### Usage: For backend Devs, Predictoors, Traders

For those who want to easily change backend components (predictoor, trader, ..)

- [Backend-dev-local](READMEs/backend-dev-local.md) -- Local components
- [Backend-dev-remote](READMEs/backend-dev-remote.md) -- Remote components


# Development

### Development: How to Iterate

Iterate by changing code, instructions in "Usage for backend devs" section.


### Development: Testing

In console:
```console
#run a single test
pytest ocean_lib/models/test/test_data_nft_factory.py::test_start_multiple_order

#run all tests in a file
pytest ocean_lib/models/test/test_data_nft_factory.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

### Development: Release Process

(FIXME)