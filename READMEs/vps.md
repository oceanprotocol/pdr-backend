<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# VPS Backend Dev

This README shows how to
- Set up an Azure Ubuntu VPS (Virtual Private Server)
- Run Barge on the VPS
- Run sim/bots or pytest using the VPS. (In fact, one VPS per flow)


## 1. Locally, install pdr-backend

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

## 2. Setup VPS

### In Azure Portal, Create new VPS

Create a new Ubuntu VM via Azure portal, as follow.

First, sign in to the [Azure portal](https://portal.azure.com/)

From Azure portal, [create new VM](https://learn.microsoft.com/en-gb/azure/virtual-machines/linux/quick-create-portal?tabs=ubuntu#create-virtual-machine). Includes:
  - your VM's username will be `azureuser`
  - download your ssh key as a file, eg `~/Desktop/myKey.pem`
  - note your IP address, eg `4.245.224.119` or `74.234.16.165`

Test it: open a new console, and ssh into new VM.
```console
ssh -i ~/Desktop/myKey.pem azureuser@4.245.224.119
# or
ssh -i ~/Desktop/myKey.pem azureuser@74.234.16.165
```

### In Azure Portal, Open ports of VPS

Running Barge, the VPS exposes these urls:
- RPC is at:
  - http://4.245.224.119:8545
  - or http://74.234.16.165:8545
- Subgraph is at:
  - http://4.245.224.119:9000/subgraphs/name/oceanprotocol/ocean-subgraph
  - or http://74.234.16.165:9000/subgraphs/name/oceanprotocol/ocean-subgraph

BUT you will not be able to see these yet, because the VPS' ports are not yet open enough. Here's how:
- Go to Azure Portal for your group
- On the bottom right, there's a table with a list of resources ("MyVm", "MyVM-ip", "MyVM-nsg", "MyVM-vnet", ..). In it, click the "-nsgs" resource.
- Now you're in the "Network Security Group" (nsg) section
- In the sidebar on left, click on "Inbound security rules"
- Click the "+ Add" button in about center middle. A side window will pop up. Keep all fields default except: "Destination port ranges" = 8545, "Protocol" = TCP, "Priority" = 100. Click "Add" button on side window bottom left. Congrats! Now you've exposed port 8545 (RPC) via TCP.
- Repeat the previous step for port 9000 (Subgraph), priority 110.

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

### Enable running docker as non-root user

In VPS console:
```console
# create the docker group if it does not exist
sudo groupadd docker

# add your user to the docker group
sudo usermod -aG docker $USER

# log in to the new docker group (to avoid having to log out / log in again; but if not enough, try to reboot):
newgrp docker
```

(Ref: https://stackoverflow.com/a/48957722)

### Install Barge In VPS

In VPS console:
```console
# install barge remotely
cd
mkdir code
cd code
git clone https://github.com/oceanprotocol/barge
cd barge
```

## 3. In VPS, Run Predictoor Barge

(If needed) SSH into VPS console:
```console
ssh -i ~/Desktop/myKey.pem azureuser@4.245.224.119
# or
ssh -i ~/Desktop/myKey.pem azureuser@74.234.16.165
```

In VPS console:
```console
# cleanup past barge
cd ~/code/barge
./cleanup.sh
rm -rf ~/.ocean
docker system prune -a -f --volumes

# run barge...
# set ganache block time to 5 seconds, try increasing this value if barge is lagging
export GANACHE_BLOCKTIME=5

# pick just OPTION 1 or 2 below, depending on your goals

# OPTION 1: for predictoor bot: run barge with all bots except predictoor. (Use this your first time through)
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph --with-pdr-trueval --with-pdr-trader --with-pdr-publisher --with-pdr-dfbuyer

# OR, OPTION 2: for unit testing: run barge with just predictoor contracts, queryable, but no agents. (Use this for step 5 - unit tests)
./start_ocean.sh --no-provider --no-dashboard --predictoor --with-thegraph
```

Wait.

Then, copy VPS' `address.json` file to local. In local console:
```console
cd

# OPTION 1: for predictoor bot
scp -i ~/Desktop/myKey.pem azureuser@4.245.224.119:.ocean/ocean-contracts/artifacts/address.json barge-predictoor-bot.address.json

# OR, OPTION 2: for unit testing
scp -i ~/Desktop/myKey.pem azureuser@74.234.16.165:.ocean/ocean-contracts/artifacts/address.json barge-pytest.address.json
```

We give the address file a unique name, vs just "address.json". This keeps it distinct from the address file for _second_ Barge VM we run for pytest (details below).

Confirm that `barge-predictoor-bot.address.json` has a "development" entry. In local console:
```console
grep development ~/barge-predictoor-bot.address.json
# or
grep development ~/barge-pytest.address.json
```

It should return:
```text
  "development": {
```

If it returns nothing, then contracts have not yet been deployed to ganache. It's either (i) you need to wait longer (ii) Barge had an issue and you need to restart it or debug.

## 4. Locally, Run Predictoor Bot (OPTION 1)

### Set envvars

In local console:
```console
# set up virtualenv (if needed)
cd ~/code/pdr-backend
source venv/bin/activate

export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58" # addr for key=0xc594.. is 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
```

### Set PPSS

Let's configure the yaml file. In console:
```console
cp ppss.yaml my_ppss.yaml
```

In `my_ppss.yaml` file, in `web3_pp` ->  `barge-predictoor-bot` section:
- change the urls and addresses as needed to reflect your VPS
- including: set the `stake_token` value to the output of the following: `grep --after-context=10 development ~/barge-predictoor-bot.address.json|grep Ocean|sed -e 's/.*0x/export STAKE_TOKEN=0x/'| sed -e 's/",//'`. (Or get the value from `~/barge-predictoor-bot.address.json`, in `"development"` -> `"Ocean"` entry.)

### Run pdr bot

Then, run a bot with modeling-on-the fly (approach 3). In console:
```console
pdr predictoor 3 my_ppss.yaml barge-predictoor-bot
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.
- It has behavior to maximize accuracy without missing submission deadlines, as follows. 60 seconds before predictions are due, it will build a model then submit a prediction. It will repeat submissions every few seconds until the deadline.
- It does this for every 5-minute epoch.

(You can track at finer resolution by writing more logs to the [code](../pdr_backend/predictoor/approach3/predictoor_agent3.py), or [querying Predictoor subgraph](subgraph.md).)


## 5. Locally, Run Tests (OPTION 2)

### Set up a second VPS / Barge

In steps 2 & 3 above, we had set up a _first_ VPS & Barge, for predictoor bot.
- Assume its IP address is 4.245.224.119

Now, repeat 2 & 3 above, to up a _second_ VPS & Barge, for local testing. 
- Give it the same key as the first barge.
- Assume its IP address is 74.234.16.165
- The "OR" options in sections 2 above use this second IP address. Therefore you can go through the flow with simple copy-and-pastes.

### Set envvars

In local console:
```console
# set up virtualenv (if needed)
cd ~/code/pdr-backend
source venv/bin/activate

# same private key as 'run predictoor bot'
export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58" # addr for key=0xc594.. is 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260

# Unit tests default to using "development" network. So, override!
export NETWORK_OVERRIDE=barge-pytest
```

### Set PPSS

Whereas most READMEs copy `ppss.yaml` to `my_ppss.yaml`, for development we typically want to operate directly on the original one.

In `ppss.yaml` file, in `web3_pp` ->  `barge-pytest` section: (note the different barge section)
- change the urls and addresses as needed to reflect your VPS
- including: set the `stake_token` value to the output of the following: `grep --after-context=10 development ~/barge-pytest.address.json|grep Ocean|sed -e 's/.*0x/stake_token: \"0x/'| sed -e 's/",//'`. (Or get the value from `~/barge-pytest.address.json`, in `"development"` -> `"Ocean"` entry.)


### Run tests

In work console, run tests:
```console
# (ensure PRIVATE_KEY set as above)

# run a single test. The "-s" is for more output.
# note that pytest does dynamic type-checking too:)
pytest pdr_backend/util/test_noganache/test_util_constants.py::test_util_constants -s

# run all tests in a file
pytest pdr_backend/util/test_noganache/test_util_constants.py -s

# run a single test that flexes network connection
pytest pdr_backend/util/test_ganache/test_contract.py::test_get_contract_filename -s

# run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:
```console
# mypy does static type-checking and more. Configure it via mypy.ini
mypy ./

# run linting on code style. Configure it via .pylintrc.
pylint pdr_backend/*

# auto-fix some pylint complaints like whitespace
black ./
```
