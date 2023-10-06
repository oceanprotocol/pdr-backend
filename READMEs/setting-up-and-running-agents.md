# Setting up and Running pdr-backend agents

This guide explains the process of setting up and running any bot (agent) locally. This example uses Sapphire testnet. However, by modifying the environment variables, you can seamlessly run the bot (agent) on the mainnet.

## Initial Setup

### Getting Tokens

Sapphire accounts and wallets follow EVM standard.

Your wallet account on Sapphire needs both ROSE (for gas) and OCEAN (for using Predictoor).

- On Sapphire testnet, get (fake) [ROSE & OCEAN via the faucet guide](./testnet-faucet.md).
- On Sapphire mainnet, get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide].(get-ocean-on-sapphire.md)

### Repository and Environment Variables

#### Install pdr-backend

Follow the instructions from [install pdr-backend](./install.md)

#### Configure Environment variables

Set the following environment variables:

```shell
export PRIVATE_KEY=PK_HERE
export PAIR_FILTER=BTC/TUSD
export TIMEFRAME_FILTER=5m
export SOURCE_FILTER=binance
export RPC_URL=https://testnet.sapphire.oasis.dev
export SUBGRAPH_URL=https://v4.subgraph.oasis-sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph/graphql
export STAKE_TOKEN=ADDRESS_OF_OCEAN_TOKEN
```

To learn more about the available enviroment variables check out the [Environment Variables (Envvars)](./envvars.md) guide.

If you're going to run the bot on testnet, set:

```shell
export OWNER_ADDRS=0xe02a421dfc549336d47efee85699bd0a3da7d6ff
```

If you're going to run the bot on mainnet, set:

```shell
export OWNER_ADDRS=0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703
```

This is the wallet address of the OPF deployer.

### Configure the Bot (Agent)

Configure the bot (agent) by following the instructions from the agent's readme that you're going to deploy:

[Predictoor README](READMEs/predictoor.md)
[Trader README](READMEs/trader.md)

## Running locally on any machine with pm2

Firstly, run the bot (agent) to make sure there are no errors and the agent is working as expected:

```bash
python pdr_backend/<agent>/main.py
```

Use `pm2` or other solutions to continously keep `main.py` running. Here's how you can do it with `pm2`:

Install `pm2` globally via `npm`.

```bash
npm install pm2 -g
```

Then, use `pm2 start` to run the script.

```bash
pm2 start main.py --name "pdr-backend-<agentname>"
```

Replace `agentname` with the name of the agent you're going to run.

Other useful commands:

- `pm2 ls` - lists running processes
- `pm2 logs` - display the logs of all the running processes

You can find more [on pm2's official website](https://pm2.keymetrics.io/docs/usage/quick-start/)