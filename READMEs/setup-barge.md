<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

## Set up barge

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge
git checkout predictoor # use barge's predictoor branch (for now)

# (optional) Clean up previous Ocean-related containers
./cleanup.sh
```

To run Barge with all of its predictoor-related arguments is the following. But DO NOT RUN this right now!! Since you might want to run a version without running all of those components. We'll specify in the appropriate place.
```console
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

When barge runs, it will auto-publish DT3 tokens. Currently this is {`BTC/TUSD`, Binance, 5min}, {`ETH/USDT`, Kraken, 5min} and {`XRP/USDT`, Binance, 5min}.

