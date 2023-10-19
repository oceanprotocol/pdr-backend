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
export PRIVATE_KEY=<your PRIVATE_KEY>
export ADDRESS_FILE="${HOME}/.ocean/ocean-contracts/artifacts/address.json"
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

If you're running a **predictoor** bot:
- If random predictions: typically you have nothing else to configure. 
- If model-based: tune with help of [dynamic model](./dynamic-model.md) or [static model](static-model.md) READMEs.
- And for further tuning: the [local predictoor README](localpredictoor-localnet.md) has more options.

If you're running a **trader** bot:
- Typically you have nothing else to configure.
- And for further tuning: the [local trader README](localtrader-localnet.md) has more options.

## Run Bot

[PM2](https://pm2.keymetrics.io/docs/usage/quick-start/) is "a daemon process manager that will help you manage and keep your application online."

This section shows how to use PM2 to run bots. It uses predictoor approach 1; other bots are nearly identical.

First, run the bot _without_ PM2 to ensure it's working as expected:

```console
python pdr_backend/predictoor/main.py 1
```

From here on, we'll use PM2. It will keep `main.py` running continuously.

First, install PM2 globally via `npm`.

```console
npm install pm2 -g
```

Next, use `pm2 start <script> -- <arg1> <arg..>` to run the bot.

```console
pm2 start pdr_backend/predictoor/main.py -- 1
```

Next, use `pm2 ls` to list running processes:

```console
pm2 ls

# output looks a bit like:
# ┌────┬─────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
# │ id │ name    │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
# ├────┼─────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
# │ 0  │ main    │ default     │ N/A     │ fork    │ 53874    │ 3m     │ 361  │ online    │ 0%       │ 138.0mb  │ trentmc  │ disabled │
# └────┴─────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
```

Next, use `pm2 logs <id>` to see the output log for the main.py. For example:
```console
pm logs 0

# output looks a bit like:
# 0|main  | Take_step() begin.
# 0|main  |   block_number=3046274, prev=3046274
# 0|main  |   Done step: block_number hasn't advanced yet. So sleep.
```

(Press ctrl-c to stop printing logs to stdout.)

Finally, use `pm2 stop <id>` to stop the process.
```console
pm2 stop 0
```

For more details on PM2:
- use `pm2 help` and `pm2 <command> help`
- and see [PM2 docs](https://pm2.keymetrics.io/docs/usage/quick-start/)

## Next step

You're now running a local bot on a remote network. Congrats!

Your next step is to run a _remote_ bot on a remote testnet. [Here's the README](./remotebot-remotenet.md).

(Note: you could always skip running a remote bot, and instead only run local bots on testnet and mainnet via this README. However, this requires your local machine to be continuously running bots. We recommend running remote bots.)

## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Parent trader README: trader.md](./trader.md)
- [Root README](../README.md)
