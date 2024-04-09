<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Predictoor Bot

This README shows how to earn $ by running a predictoor bot on mainnet.

**Main flow:**

1. **[Install](#1-install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#2-simulate-modeling-and-trading)**
1. **[Run bot on testnet](#3-run-predictoor-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](#4-run-predictoor-bot-on-sapphire-mainnet)**
1. **[Claim payout](#5-claim-payout)**

Once you're done the main flow, you can go beyond, with any of:

- [Optimize model](#optimize-model)
- [Right-size staking](#right-size-staking)
- [Run local network](#run-local-network)
- [Run many bots](#run-many-bots). Steps: [give keys](#many-bots-give-keys), [templates](#many-bots-generate-templates), [deploy agents](#many-bots-deploy-agents), [monitor agents](#many-bots-monitor-agents), [destroy agents](#many-bots-destroy-agents)

## 1. Install pdr-backend Repo

In a new console:

```console
# clone the repo and enter into it
git clone https://github.com/oceanprotocol/pdr-backend
cd pdr-backend

# Create & activate virtualenv
python -m venv venv
source venv/bin/activate

# Install modules in the environment
pip install -r requirements.txt

#add pwd to bash path
export PATH=$PATH:.
```

You need a local copy of Ocean contract addresses [`address.json`](https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json). In console:
```console
# make directory if needed
mkdir -p ~/.ocean; mkdir -p ~/.ocean/ocean-contracts; mkdir -p ~/.ocean/ocean-contracts/artifacts/

# copy from github to local directory. Or, use wget if Linux. Or, download via browser.
curl https://github.com/oceanprotocol/contracts/blob/main/addresses/address.json -o ~/.ocean/ocean-contracts/artifacts/address.json
```

If you're running MacOS, then in console:

```console
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib
```

## 2. Simulate Modeling and Trading

Simulation allows us to quickly build intuition, and assess the performance of the data / predicting / trading strategy (backtest).

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit.

```console
cp ppss.yaml my_ppss.yaml
```

Let's simulate! In console:

```console
pdr sim my_ppss.yaml
```

What it does:

1. Set simulation parameters.
1. Grab historical price data from exchanges and stores in `parquet_data/` dir. It re-uses any previously saved data.
1. Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict
   - Trade
   - Plot profit versus time, more
   - Log to console and `logs/out_<time>.txt`

"Predict" actions are _two-sided_: it does one "up" prediction tx, and one "down" tx, with more stake to the higher-confidence direction. Two-sided is more profitable than one-sided prediction.

By default, simulation uses a linear model inputting prices of the previous 2-10 epochs as inputs (autoregressive_n), just BTC close price as input, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in `my_ppss.yaml`.

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a big difference too.

To see simulation CLI options: `pdr sim -h`.

Simulation uses Python [logging](https://docs.python.org/3/howto/logging.html) framework. Configure it via [`logging.yaml`](../logging.yaml). [Here's](https://medium.com/@cyberdud3/a-step-by-step-guide-to-configuring-python-logging-with-yaml-files-914baea5a0e5) a tutorial on yaml settings.

## 3. Run Predictoor Bot on Sapphire Testnet

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our predictoor bot running on testnet first.

The bot does two-sided predictions, like in simulation. This also means it needs two Ethereum accounts, with keys PRIVATE_KEY and PRIVATE_KEY2.

First, tokens! You need (fake) ROSE to pay for gas, and (fake) OCEAN to stake and earn, for both accounts. [Get them here](testnet-faucet.md).

Then, copy & paste your private keys as envvars. In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY 1>
export PRIVATE_KEY2=<YOUR_PRIVATE_KEY 2>
```

Next, update `my_ppss.yaml` as desired.

Then, run a bot with modeling-on-the fly (approach 2). In console:

```console
pdr predictoor 2 my_ppss.yaml sapphire-testnet
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.

At every 5m/1h epoch, it builds & submits >1 times, to maximize accuracy without missing submission deadlines. Specifically: 60 s before predictions are due, it builds a model then prediction txs for up and for down (with stake for each). It repeats this until the deadline.

It logs to console, and to `logs/out_<time>.txt`. Like simulation, it uses Python logging framework, configurable in `logging.yaml`.

To see predictoor CLI options: `pdr predictoor -h`

The CLI has support tools too. Learn about each via:

- `pdr get_predictoor_info -h`
- `pdr get_predictions_info -h`
- and more yet; type `pdr -h` to see

You can track behavior at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/predictoor_agent.py), or [querying Predictoor subgraph](subgraph.md).

## 4. Run Predictoor Bot on Sapphire Mainnet

Time to make it real: let's get our bot running on Sapphire _mainnet_.

First, real tokens! Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md), for each of your two accounts.

Then, copy & paste your private keys as envvars. (You can skip this if keys are same as testnet.) In console:

```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY 1>
export PRIVATE_KEY2=<YOUR_PRIVATE_KEY 2>
```

Update `my_ppss.yaml` as desired.

Then, run the bot. In console:

```console
pdr predictoor 2 my_ppss.yaml sapphire-mainnet
```

This is where there's real $ at stake. Good luck!

Track performance, as in testnet.

## 5. Claim Payout

When running predictoors on mainnet, you have the potential to earn $.

**[Here](payout.md)** are instructions to claim your earnings.

Congrats! You've gone through all the essential steps to earn $ by running a predictoor bot on mainnet.

The next sections describe how to go beyond, by optimizing the model and more.

# Optimize model

The idea: make your own model, tuned for accuracy, which in turn will optimize it for $. Here's how:

1. Fork `pdr-backend` repo.
1. Change predictoor approach 2 modeling code as you wish, while iterating with simulation.
1. Bring your model as a Predictoor bot to testnet then mainnet.

# Right-size staking

The default predictoor approaches have a fixed-amount stake with a small default value. Yet the more you stake, the more you can earn, up to a point: if you stake too much then the losses from slashing exceed wins from rewards.

So what's the right amount?

The blog post ["Right-Size Staking in Ocean Predictoor"](https://blog.oceanprotocol.com/rewards-mechanisms-of-ocean-predictoor-6f76c942baf7) explores this in great detail, and gives practical guidance. You can implement some or all of the ideas.

# Run local network

To get extra-fast block iterations, you can run a local test network (with local bots). It does take a bit more up-front setup. Get started [here](barge.md).

# Run many bots

The instructions above are on running a single bot on a single prediction feed. Yet Predictoor has _many_ feeds. You could manually run & monitor one bot per feed. But this gets tedious beyond a few feeds. Here, we show how to run _many_ bots by containerizing each bot, and using Kubernetes to manage them via the `deployer` CLI utility.

`deployer` is a streamlined CLI utility designed for efficiently generating and managing agent deployments.

This section shows how to use `deployer` to deploy bots on testnet.

## Many bots: config

The config that will be deployed can be found in `ppss.yaml` under `deployment_configs` section. You can create your own config by copying the existing one and modifying it as you wish. For the sake of this example, the existing config will be used.

`ppss.yaml`:

```yaml
deployment_configs:
  testnet_predictoor_deployment:
    cpu: "1"
    memory: "512Mi"
    source: "binance"
    type: "predictoor"
    approach: 2
    network: "sapphire-testnet"
    s_until_epoch_end: 20
    pdr_backend_image_source: "oceanprotocol/pdr-backend:latest"
    agents:
      - pair: "BTC/USDT"
        stake_amt: 0.1
        timeframe: 5m
        approach: 1
      - pair: "ETH/USDT"
        stake_amt: 1
        timeframe: 1h
        s_until_epoch_end: 100
```

## Many bots: give keys

Create a `.keys.json` file and add the following:

```json
{
  "testnet_predictoor_deployment": ["pk1", "pk2"]
}
```

Each agent requires a private key. If you have fewer private keys than number of agents, the tool will create new wallets and update the `.keys.json` file. Make sure the wallets have enough ROSE and OCEAN to pay for gas and stake.

## Many bots: generate templates

The `generate` command is used to create deployment template files based on a configuration file.

Execute the following command to generate the deployment templates:

```console
pdr deployer generate ppss.yaml testnet_predictoor_deployment k8s testnet_deployments
```

Where `ppss.yaml` is the config file, `testnet_predictoor_deployment` is the config name, `k8s` is the deployment method, and `testnet_deployments` is the output directory for the generated files.

Available deployment methods are `k8s`.

## Many bots: deploy agents

The `deploy` command is used to deploy agents that follow the generated templates.

Execute the following command to deploy the generated config:

```console
pdr deployer deploy testnet_predictoor_deployment -p gcp -r europe-west2 --project-id
```

Where `testnet_predictoor_deployment` is the config name.

Since k8s is used as the deployment method, the following additional parameters are required:

- `-p` or `--provider`: The cloud provider to use. Available options are `gcp`, `aws`, and `azure`.
- `-r` or `--region`: The region to deploy to.
- `--project-id`: The cloud provider project id. Only required for GCP.
- `--resource-group`: The cloud provider resource group. Only required Azure.
- `--subscription-id`: The cloud provider subscription id. Only required for Azure.

## Many bots: monitor agents

The `logs` command is used to retrieve logs from deployed agents.

Execute the following command to retrieve logs from the deployed agents:

```console
pdr deployer logs testnet_predictoor_deployment
```

Where `testnet_predictoor_deployment` is the config name.

## Many bots: destroy agents

The `destroy` command is used to destroy agents deployed based on a specified configuration.

Execute the following command to destroy the deployed agents:

```console
pdr deployer destroy testnet_predictoor_deployment
```

Where `testnet_predictoor_deployment` is the config name.

## Warning

You will lose money as a predictoor if your $ out exceeds your $ in. If you have low accuracy you’ll have your stake slashed a lot. Do account for gas fees, compute costs, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
