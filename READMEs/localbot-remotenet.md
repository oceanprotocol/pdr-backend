# Run Local Predictoor/Trader Bot, Remote Network

This README describes:
- Running a *local predictoor or trader* bot (agent)
- On a *remote network* where other bots are remote
- It uses containers

This example uses Sapphire testnet; you can modify envvars to run on Sapphire maainnet.

**Steps:**

1. **[Get tokens](#get-tokens)**
2. **Setup & run predictoor/trader bot**
    - [Install it](#install-bot)
    - [Set envvars](#set-envvars)
    - [Configure it](#configure-bot)
    - [Run it](#run-bot)

## Get Tokens

[See get-tokens.md](./get-tokens.md).

## Install Bot

The predictoor & trader bots run code that lives in `pdr-backend` repo.

[Install pdr-backend](install.md).

## Set Envvars

Set the following:

```console
export PRIVATE_KEY=PK_HERE
export PAIR_FILTER=BTC/USDT
export TIMEFRAME_FILTER=5m
export SOURCE_FILTER=binance
```

If Sapphire testnet:
```console
export RPC_URL=https://testnet.sapphire.oasis.dev
export SUBGRAPH_URL=https://v4.subgraph.sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
export STAKE_TOKEN=0x973e69303259B0c2543a38665122b773D28405fB # (fake) OCEAN token address
export OWNER_ADDRS=0xe02a421dfc549336d47efee85699bd0a3da7d6ff # OPF deployer address
```

If Sapphire mainnet:
```console
export RPC_URL=https://sapphire.oasis.io
export SUBGRAPH_URL=https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph
export STAKE_TOKEN=0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520 # OCEAN token address
export OWNER_ADDRS=0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703 # OPF deployer address
```

([Envvar docs](./envvars.md) have more details.)

## Configure Bot

If you're running a **predictoor** bot: choose between random or model-based and make other configurations with guidance in the [local predictoor README](localpredictoor-localnet.md).

If you're running a **trader** bot: make other configurations with guidance in the [local trader README](localtrader-localnet.md).

## Run Bot

First, run the bot _without_ `pm2` to ensure it's working as expected:

```console
python pdr_backend/<agent>/main.py
```

From here on we'll use the `pm2` tool. It will keep `main.py` running continuously.

First, install `pm2` globally via `npm`.

```console
npm install pm2 -g
```

Then, use `pm2 start` to run the script.

```console
pm2 start main.py --name "pdr-backend-<botname>"
```

Replace `botname` with the name of the bot you're going to run.

Other useful commands:

- `pm2 ls` - lists running processes
- `pm2 logs` - display the logs of all the running processes

[The pm2 docs](https://pm2.keymetrics.io/docs/usage/quick-start/) have more details.
