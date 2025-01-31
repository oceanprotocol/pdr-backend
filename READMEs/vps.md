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
export PATH=$PATH:.

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
  - `http://4.245.224.119:8545`
  - or `http://74.234.16.165:8545`
- Subgraph is at:
  - `http://4.245.224.119:9000/subgraphs/name/oceanprotocol/ocean-subgraph`
  - or `http://74.234.16.165:9000/subgraphs/name/oceanprotocol/ocean-subgraph`
  - Go there, then copy & paste in the query from [subgraph.md](subgraph.md)

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

(Ref: `https://stackoverflow.com/a/48957722`)

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

## 4. Locally, Run Predictoor Bot (OPTION 1)

### Set envvars

In local console:

```console
# set up virtualenv (if needed)
cd ~/code/pdr-backend
source venv/bin/activate
export PATH=$PATH:.

export PRIVATE_KEY="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58" # addr for key=0xc594.. is 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
```

### Set PPSS

Let's configure the yaml file. In console:

```console
cp ppss.yaml my_ppss.yaml
```

In `my_ppss.yaml` file, in `web3_pp` -> `development` section:

- change the urls and addresses as needed to reflect your VPS


### Run trader bot

In console:

```console
pdr trader my_ppss.yaml livemock
```

Or, to be fancier: (a) add `nohup` so that the run keeps going if the ssh session closes, and (b) output to out.txt (c) observe output 
```console
# start bot
nohup pdr trader my_ppss.yaml livemock 1>out.txt 2>&1 &

# observe output
tail -f out.txt
```

Your bot is running, congrats! Sit back and watch it in action. It will loop continuously.

You can track at finer resolution by writing more logs to the code.

## Locally, Run tests

In work console, run tests:

```console
# (ensure PRIVATE_KEY set as above)

# run a single test. The "-s" is for more output.
# note that pytest does dynamic type-checking too:)
pytest pdr_backend/util/test_noganache/test_util_constants.py::test_util_constants -s

# run all tests in a file
pytest pdr_backend/util/test_noganache/test_util_constants.py -s

# run all regular tests; see details on pytest markers to select specific suites
pytest
```

In work console, run linting checks:

```console
# mypy does static type-checking and more. Configure it via mypy.ini
mypy ./

# run linting on code style. Configure it via .pylintrc.
pylint *

# auto-fix some pylint complaints like whitespace
black ./
```
