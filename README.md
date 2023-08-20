<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend: Predictoor Backend

## What's pdr-backend

pdr-backend implements all of the agents of the Predictoor ecosystem.

Each agent has a directory:
- `predictoor` - agent that submits individual predictions
- `trader` - agent that buys aggregated predictions & trades
- `trueval` - agent that reports true values to contract
- `dfbuyer` - agent that buys aggregate predictions on behalf of Data Farming

Other directories:
- `utils` - tools for use by any agent

## How to use pdr-backend

- If you are a **predictoor**, see [Predictoor README](pdr_backend/predictoor/README.md)
- If you are a **trader**, do [Trader README](pdr_backend/trader/README.md)
- If you are a **frontend dev** working on predictoor.ai: do [Frontend-Dev README](READMEs/frontend-dev.md)
- If you are a **backend dev** working on `pdr-backend` itself: do [Backend-Dev README](READMEs/backend-dev.md)

