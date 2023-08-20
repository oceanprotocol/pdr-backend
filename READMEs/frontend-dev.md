<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Usage for Frontend Devs

## 1. Introduction

This is for frontend devs who are developing predictoor.ai etc. Uses barge locally. Backend components don't change.

## 2. Install barge

Follow instructions in [barge.md "install"](barge.md#install-barge).

## 3. Run barge

In barge console:
```console
./start_ocean.sh --predictoor --with-pdr-trueval --with-pdr-trader --with-pdr-predictoor --with-pdr-publisher --with-pdr-dfbuyer
```

## 4. Run frontend

Run frontend components that talk to chain & agents in barge, via http api.

Follow instructions at https://github.com/oceanprotocol/pdr-web/
