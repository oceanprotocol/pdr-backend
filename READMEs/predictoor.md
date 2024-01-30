<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Predictoor Bot

This README shows how to earn $ by running a predictoor bot on mainnet.

1. **[Install](#install-pdr-backend-repo)**
1. **[Simulate modeling & trading](#simulate-modeling-and-trading)**
1. **[Run bot on testnet](#run-predictoor-bot-on-sapphire-testnet)**
1. **[Run bot on mainnet](#run-predictoor-bot-on-sapphire-mainnet)**
1. **[Claim payout](#claim-payout)**
1. **[Check performance](#check-performance)**

Then, you can [go beyond](#go-beyond): [optimize model](#optimize-model), [run >1 bots](#run-many-bots-at-once), and more.


## Install pdr-backend Repo

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

If you're running MacOS, then in console:
```console
codesign --force --deep --sign - venv/sapphirepy_bin/sapphirewrapper-arm64.dylib
```

## Simulate Modeling and Trading

Simulation allows us to quickly build intuition, and assess the performance of the data / predicting / trading strategy (backtest).

Copy [`ppss.yaml`](../ppss.yaml) into your own file `my_ppss.yaml` and change parameters as you see fit.

Let's simulate! In console:
```console
pdr xpmt my_ppss.yaml
```

"xpmt" is short for "experiment". (The xpmt tool is evolving beyond just simulation.)


What it does:
1. Set simulation parameters.
1. Grab historical price data from exchanges and stores in `parquet_data/` dir. It re-uses any previously saved data.
1. Run through many 5min epochs. At each epoch:
   - Build a model
   - Predict up/down
   - Trade.
   - Plot total profit versus time, and more.
   - (It logs this all to screen, and to `out*.txt`.)

The baseline settings use a linear model inputting prices of the previous 10 epochs as inputs, a simulated 0% trading fee, and a trading strategy of "buy if predict up; sell 5min later". You can play with different values in `my_ppss.yaml`.

Profit isn't guaranteed: fees, slippage and more eats into them. Model accuracy makes a big difference too.

## Run Predictoor Bot on Sapphire Testnet

Predictoor contracts run on [Oasis Sapphire](https://docs.oasis.io/dapp/sapphire/) testnet and mainnet. Sapphire is a privacy-preserving EVM-compatible L1 chain.

Let's get our bot running on testnet first.

First, tokens! You need (fake) ROSE to pay for gas, and (fake) OCEAN to stake and earn. [Get them here](testnet-faucet.md).

Then, copy & paste your private key as an envvar. In console:
```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Update `my_ppss.yaml` as desired.

Then, run a bot with modeling-on-the fly (approach 3). In console:
```console
pdr predictoor 3 my_ppss.yaml sapphire-testnet 
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.

At every 5m/1h epoch, it builds & submits >1 times, to maximize accuracy without missing submission deadlines. Specifically: 60 s before predictions are due, it builds a model then submits a prediction. It repeats this until the deadline.

The CLI has a tool to track performance. Type `pdr get_predictoor_info -h` for details.

You can track behavior at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).


## Run Predictoor Bot on Sapphire Mainnet

Time to make it real: let's get our bot running on Sapphire _mainnet_.

First, real tokens! Get [ROSE via this guide](get-rose-on-sapphire.md) and [OCEAN via this guide](get-ocean-on-sapphire.md).

Then, copy & paste your private key as an envvar. (You can skip this if it's same as testnet.) In console:
```console
export PRIVATE_KEY=<YOUR_PRIVATE_KEY>
```

Update `my_ppss.yaml` as desired.

Then, run the bot. In console:
```console
pdr predictoor 3 my_ppss.yaml sapphire-mainnet 
```

This is where there's real $ at stake. Good luck!

Track performance, as in testnet.

## Claim Payout

When running predictoors on mainnet, you have the potential to earn $.

**[Here](payout.md)** are instructions to claim your earnings.


# Go Beyond

You've gone through all the essential steps to earn $ by running a predictoor bot on mainnet.

The next sections describe how to go beyond, by optimizing the model and more.

## Optimize Model

Once you're familiar with the above, you can make your own model and optimize it for $. Here's how:
1. Fork `pdr-backend` repo.
1. Change predictoor approach3 modeling code as you wish, while iterating with simulation.
1. Bring your model as a Predictoor bot to testnet then mainnet.


## Run Many Bots at Once

`deployer` is a streamlined command-line utility designed for efficiently generating and managing agent deployments.

This section shows how to use `deployer` to deploy bots on testnet.

The config that will be deployed can be found in `ppss.yaml` under `deployment_configs` section. You can create your own config by copying the existing one and modifying it as you wish. For the sake of this example, the existing config will be used.

`ppss.yaml`:
```yaml
deployment_configs:
  testnet_predictoor_deployment:
    cpu: '1'
    memory: '512Mi'
    source: "binance"
    type: "predictoor"
    approach: 3
    network: "sapphire-testnet"
    s_until_epoch_end: 20
    pdr_backend_image_source: "oceanprotocol/pdr-backend:latest"
    agents:
      - pair: 'BTC/USDT'
        stake_amt: 0.1
        timeframe: 5m
        approach: 1
      - pair: 'ETH/USDT'
        stake_amt: 1
        timeframe: 1h
        s_until_epoch_end: 100
```

### Private Keys
Create a `.keys.json` file and add the following:
```
{
    "testnet_predictoor_deployment": ["pk1", "pk2"]
}
```

Each agent requires a private key. If you have fewer private keys than number of agents, the tool will create new wallets and update the `.keys.json` file. Make sure the wallets have enough ROSE and OCEAN to pay for gas and stake.


### Generate Templates

The `generate` command is used to create deployment template files based on a configuration file.

Execute the following command to generate the deployment templates:
```
pdr deployer generate ppss.yaml testnet_predictoor_deployment k8s testnet_deployments
```

Where `ppss.yaml` is the config file, `testnet_predictoor_deployment` is the config name, `k8s` is the deployment method, and `testnet_deployments` is the output directory for the generated files.

Available deployment methods are `k8s`.

### Deploy

The `deploy` command is used to deploy the generated templates.

Execute the following command to deploy the generated config:
```
pdr deployer deploy testnet_predictoor_deployment -p gcp -r europe-west2 --project-id
```

Where `testnet_predictoor_deployment` is the config name.

Since k8s is used as the deployment method, the following additional parameters are required:
- `-p` or `--provider`: The cloud provider to use. Available options are `gcp`, `aws`, and `azure`.
- `-r` or `--region`: The region to deploy to.
- `--project-id`: The cloud provider project id. Only required for GCP.
- `--resource-group`: The cloud provider resource group. Only required Azure.
- `--subscription-id`: The cloud provider subscription id. Only required for Azure.

### Monitoring logs

The `logs` command is used to retrieve logs from deployed agents.

Execute the following command to retrieve logs from the deployed agents:
```
pdr deployer logs testnet_predictoor_deployment
```

Where `testnet_predictoor_deployment` is the config name.

### Destroy

The `destroy` command is used to destroy agents deployed based on a specified configuration.

Execute the following command to destroy the deployed agents:
```
pdr deployer destroy testnet_predictoor_deployment
```

Where `testnet_predictoor_deployment` is the config name.

## Run Local Network

To get extra-fast block iterations, you can run a local test network (with local bots). It does take a bit more up-front setup. Get started [here](barge.md).

## Other READMEs

- [Root README](../README.md)

## Warning

You will lose money as a predictoor if your $ out exceeds your $ in. If you have low accuracy you’ll have your stake slashed a lot. Do account for gas fees, compute costs, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
