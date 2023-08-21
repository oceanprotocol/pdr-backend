<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# pdr-backend: Predictoor Backend

## Quickstart (per Stakeholder)

Main
- If you are a **predictoor**, do [Predictoor README](READMEs/predictoor.md)
- If you are a **trader**, do [Trader README](READMEs/trader.md)

Developers
- If you are a **frontend dev** working on predictoor.ai: do [Frontend-Dev README](READMEs/frontend-dev.md)
- If you are a **backend dev** working on `pdr-backend` itself: do [Backend-Dev README](READMEs/backend-dev.md)
- If you are a **publisher**: do [Publisher README](READMEs/publisher.md)

## About

The `pdr-backend` repo implements all of the agents of the Predictoor ecosystem.

Each agent has a directory:
- `predictoor` - agent that submits individual predictions
- `trader` - agent that buys aggregated predictions, then trades
- `trueval` - agent that reports true values to contract
- `dfbuyer` - agent that buys aggregate predictions on behalf of Data Farming

Other directories:
- `utils` - tools for use by any agent

The `predictoor` and `trader` agents are meant to be customized by predictoor and trader stakeholders, respectively.

