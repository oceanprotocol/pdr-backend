<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Barge Remotely on VPS

This README shows how to run Barge on an Azure Ubuntu VPS (Virtual Private Server). This is for use in backend dev, running predictoor bot, running trader bot.

1. [Setup VPS](#1-setup-vps)
   - [Create new VPS](#create-new-vps)
   - [Open ports of VPS](#open-ports-of-vps)
   - [Install Docker in VPS](#install-docker-in-vps)
   - [Install Barge in VPS](#install-barge-in-vps)
2. [Run Barge in VPS](#2-run-barge-in-vps)
3. [Install pdr-backend locally](#3-install-pdr-backend-locally)
4. [Run predictoor bot locally](#4-run-predictoor-bot-locally)
5. [Run tests locally](#5-run-tests-locally)


## 1. Setup VPS

### Create new VPS

Create a new Ubuntu VM via Azure portal, as follow.

First, sign in to the [Azure portal](https://portal.azure.com/)

From Azure portal, [create new VM](https://learn.microsoft.com/en-gb/azure/virtual-machines/linux/quick-create-portal?tabs=ubuntu#create-virtual-machine). Includes:
  - your VM's username will be `azureuser`
  - download your ssh key as a file, eg `~/Desktop/myKey.pem`
  - note your IP address, eg `4.245.224.119`

Test it: open a new console, and ssh into new VM.
```console
ssh -i ~/Desktop/myKey.pem azureuser@4.245.224.119
```


### Open ports of VPS

Running Barge, the VPS exposes these urls:
- RPC is at https://4.245.224.119:8545
- Subgraph is at http://4.245.224.119:9000/subgraphs/name/oceanprotocol/ocean-subgraph

BUT you will not be able to see these yet, because the VPS' ports are not yet open enough. Here's how:
- Go to Azure Portal for your group
- In the sidebar on left, click on "Inbound security rules"
- Click the "+ Add" button. A side window will pop up. Keep all fields default except: Protocol = TCP, port = 8545. Click "Add" button on side window bottom left. Congrats! Now you've exposed port 8545 (RPC) via TCP.
- Repeat the previous step for port 9000 (Subgraph).

(Ref: these [instructions](https://learn.microsoft.com/en-us/answers/questions/1190066/how-can-i-open-a-port-in-azure-so-that-a-constant).)


### Install Docker in VPS

(Draws on [these](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) Docker install instructions.)

In VPS console:
```console
# update ubuntu
sudo apt-get -y update

# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# add the repo to apt sources
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install latest Docker version
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
```

### Install Barge In VPS

This is the usual approach. We repeat for convenience.

In VPS console:
```console
## install barge remotely
cd code
git clone https://github.com/oceanprotocol/barge
git checkout predictoor
```

## 2. Run Barge in VPS

This is the usual approach. We repeat for convenience.

In VPS console:
```console
## cleanup past barge
rm -rf ~/.ocean
./cleanup.sh
docker system prune -a --volumes

## run barge
# set ganache block time to 5 seconds, try increasing this value if barge is lagging
export GANACHE_BLOCKTIME=5

#run barge with all bots except predictoor
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer
```

Wait.

Then, copy VPS' ocean.py to local

In local console:
```console
cd
scp -i ~/Desktop/myKey.pem azureuser@4.245.224.119:.ocean/ocean-contracts/artifacts/address.json .
```

## 3. Install pdr-backend Locally

This is the usual approach. We repeat for convenience.

In local console:
```console
# clone the repo and enter into it
cd ~/code
git clone https://github.com/oceanprotocol/pdr-backend
cd pdr-backend

# Create & activate virtualenv
python -m venv venv
source venv/bin/activate

# Install modules in the environment
pip install -r requirements.txt
```

## 4. Run Predictoor Bot Locally

In local console:
```console
# Setup virtualenv (if needed)
cd ~/code/pdr-backend
source venv/bin/activate

# Set envvars
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
export ADDRESS_FILE="${HOME}/address.json" # from scp to local

export RPC_URL=https://4.245.224.119:8545 # from VPS 
export SUBGRAPH_URL="http://4.245.224.119:9000/subgraphs/name/oceanprotocol/ocean-subgraph" # from VPS

#for predictoor bot
export PAIR_FILTER=BTC/USDT
export TIMEFRAME_FILTER=5m
export SOURCE_FILTER=binance

export OWNER_ADDRS=0xe02a421dfc549336d47efee85699bd0a3da7d6ff # OPF deployer address #FIXME is this correct?
```

Open address.json, find the "development" : "Ocean" entry, and paste it here. Eexample:
```console
export STAKE_TOKEN=0x2473f4F7bf40ed9310838edFCA6262C17A59DF64 #OCEAN
```

([envvars.md](envvars.md) has details.)


Then, run a bot with modeling-on-the fly (approach 3). In console:
```console
python pdr_backend/predictoor/main.py 3
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.
- It has behavior to maximize accuracy without missing submission deadlines, as follows. 60 seconds before predictions are due, it will build a model then submit a prediction. It will repeat submissions every few seconds until the deadline.
- It does this for every 5-minute epoch.

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)


## 5. Run Tests Locally

In work console, run tests:
```console
#(ensure envvars set as above)

#run a single test
pytest pdr_backend/util/test/test_constants.py::test_constants1

#run all tests in a file
pytest pdr_backend/util/test/test_constants.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:
```console
#run static type-checking. By default, uses config mypy.ini. Note: pytest does dynamic type-checking.
mypy ./

#run linting on code style
pylint pdr_backend/*

#auto-fix some pylint complaints
black ./
```
