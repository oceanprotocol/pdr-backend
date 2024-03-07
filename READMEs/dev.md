<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Backend Devs

This is for core devs to improve pdr-backend repo itself.

## Install pdr-backend

Follow directions to install pdr-backend in [predictoor.md](predictoor.md)

## Setup Barge

**Local barge.** If you're on ubuntu, you can run barge locally.

- First, [install barge](barge.md#install-barge).
- Then, run it. In barge console: `./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph`

**Or, remote barge.** If you're on MacOS or Windows, run barge on VPS.

- Follow the instructions in [vps.md](vps.md)

### Setup dev environment

Open a new "work" console and:

```console
# Setup virtualenv
cd pdr-backend
source venv/bin/activate

# Set PRIVATE_KEY
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"

# Unit tests default to using "development" network -- a locally-run barge.
# If you need another network such as barge on VPS, then override the endpoints for the development network
```

All other settings are in [`ppss.yaml`](../ppss.yaml). Some of these are used in unit tests. Whereas most READMEs make a copy `my_ppss.yaml`, for development we typically want to operate directly on `ppss.yaml`.

### Local Usage: Testing & linting

In work console, run tests:

```console
# (ensure PRIVATE_KEY set as above)

# run a single test. The "-s" is for more output.
# note that pytest does dynamic type-checking too:)
pytest pdr_backend/util/test_noganache/test_util_constants.py::test_util_constants -s

# run all tests in a file
pytest pdr_backend/util/test_noganache/test_util_constants.py -s

# run a single test that flexes network connection
pytest pdr_backend/util/test_ganache/test_contract.py::test_get_contract_filename -s

# run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:

```console
# mypy does static type-checking and more. Configure it via mypy.ini
mypy ./

# run linting on code style. Configure it via .pylintrc.
pylint *

# auto-fix some pylint complaints like whitespace
black ./
```

=======
Check code coverage:

```console
coverage run --omit="*test*" -m pytest # Run all. For subset, add eg: pdr_backend/lake
coverage report # show results
```

### Local Usage: Run a custom agent

Let's say you want to change the trader agent, and use off-the-shelf agents for everything else. Here's how.

In barge console:

```console
# (Hit ctrl-c to stop existing barge)

# Run all agents except trader
./start_ocean.sh --predictoor --with-thegraph --with-pdr-trueval --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

In work console:

```console
#(ensure envvars set as above)

# run trader agent, approach 1
pdr trader 1 ppss.yaml development
# or
pdr trader 1 ppss.yaml barge-pytest
```

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)

## Remote Usage

In the CLI, simply point to a different network:

```console
# run on testnet
pdr trader ppss.yaml sapphire-testnet

# or, run on mainnet
pdr trader ppss.yaml sapphire-mainnet
```
