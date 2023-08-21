# Setting up and Running pdr-backend locally and on Azure

This guide explains the process of setting up and running any agent locally and on Azure Container Instance for continuous execution. This example uses Sapphire testnet. However, by modifying the environment variables, you can seamlessly run the agent on the mainnet.

## Initial Setup

### Getting Test Tokens

The Sapphire network is EVM (Ethereum Virtual Machine) compatible, you'll need to fund your EVM compatible wallet from the faucet in order to submit predictions to the smart contract. Follow the [faucet guide](./testnet-faucet.md) to fund your wallet.

### Repository and Environment Variables

#### Install pdr-backend

Follow the instructions from [install pdr-backend](./install.md)

#### Configure Environment variables

Set the following environment variables:

- PRIVATE_KEY: Set it to the private key of the wallet you're going to use.
- PAIR_FILTER: List of pairs to filter (separated by comma), if empty the app will fetch all available pairs. For this example, set it to `"BTC/TUSD"`.
- TIMEFRAME_FILTER: Timeframes to filter (separated by comma), if empty the app will fetch all available timeframes. For this example, set it to `5m`.
- SOURCE_FILTER: Price sources filter (separated by comma), if empty the app will fetch all available sources. For this example, set it to `binance`
- RPC_URL: The RPC URL of the network, set this to Sapphire testnet Websocket RPC URL: `https://testnet.sapphire.oasis.dev`
- SUBGRAPH_URL: The Ocean subgraph url, set this to Sapphire testnet subgraph URL: `https://v4.subgraph.oasis-sapphire-testnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph/graphql`

If you plan to run a predictoor agent, you need to set the `STAKE_TOKEN`:

- STAKE_TOKEN: List of Token contract addresses to be used to stake, if empty the app will try to stake with any token. Set this to testOCEAN token address: `"["0x973e69303259B0c2543a38665122b773D28405fB"]"`

### Configure the Agent

Configure the agent by following the instructions from the agent's readme that you're going to deploy:

[Predictoor README](READMEs/predictoor.md)
[Trader README](READMEs/trader.md)

## Running locally on any machine with pm2

Firstly, run the agent to make sure there are no errors and the agent is working as expected:

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

## Build a container image

Make sure you have either Docker or Podman installed in your system. Run one of the following commands from the root directory of the repo:

```bash
# if docker is installed
docker build -t pdr-backend-<agentname>:latest .
# if podman is installed
podman build -t pdr-backend-<agentname>:latest .
```

Replace `agentname` with the name of the agent you're going to run. This command builds the container image using the Dockerfile in the current directory and tags it as `pdr-backend-<agentname>:latest`. You can use any tag you'd like.

There are many options available for deploying the container image. Some of them include:
- [Heroku - Container Registry & Runtime (Docker Deploys)](https://devcenter.heroku.com/articles/container-registry-and-runtime)
- [AWS -  Deploy Docker Containers on Amazon ECS](https://aws.amazon.com/getting-started/hands-on/deploy-docker-containers/)
- [Google Cloud - Deploying to Cloud Run](https://cloud.google.com/run/docs/deploying)
- [Azure - Azure Container Instances (ACI)](#running-on-azure-as-a-container)

The following example demonstrates deploying the agent as a container on Azure.

## Running on Azure as a Container

> **Warning**
> The information provided in this documentation is up to date as of August 2023. If you encounter any issues or need the latest instructions, please refer to [Azure's official documentation](https://learn.microsoft.com/en-us/azure/app-service/tutorial-custom-container?tabs=azure-cli&pivots=container-linux) on running containers.

In order to run the the agent on Azure, you will have to build a container, upload it to Azure Container Registry, and finally run it using Azure Container Instances.

### Install Azure CLI

Follow the instructions from [Microsoft's website](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli#install) to install. Then type `az login` in the terminal to log-in.

### Build a container image

Follow the instructions in [Building a container image](#build-a-container-image) section.

### Setting up Azure Container Registry (ACR)

Next, create a container registry on Azure where you'll upload your container image.

[Click here to view the documentation for `az acr create`](https://learn.microsoft.com/en-us/cli/azure/acr?view=azure-cli-latest#az-acr-create)

```bash
az acr create --name <ACR_NAME> --resource-group <resource group name> --sku <sku>
```

- --name: The name of the container registry. It should be specified in lower case. You will need it in the next step.
- --resource-group: The name of the resource group where you want to create the ACR. You can learn more about managing resource groups from [Azure's documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal).
- --sku: Pricing tier for ACR, accepted values are: `Basic`, `Standard`, `Premium`.

### Pushing the container image to ACR

You can now push your container image to ACR. Don't forget to replace `<acr_name>` with the name you gave to your ACR in the previous step.

Firstly, you'll need to provide docker or podman with access to your ACR.

[Click here to view the documentation for `az acr login`](https://learn.microsoft.com/en-us/cli/azure/acr?view=azure-cli-latest#az-acr-login)

```bash
az acr login --name <acr_name>
```

> **Note**
> If you need to get access token you can use `--expose-token` parameter and login using `podman/docker login` command.

Push the container image to the registry.

```bash
# docker
docker tag pdr-backend-<agentname>:latest <acr_name>.azurecr.io/pdr-backend-<agentname>:latest
docker push <acr_name>.azurecr.io/pdr-backend-<agentname>:latest
```

```bash
# podman
podman tag pdr-backend-<agentname>:latest <acr_name>.azurecr.io/pdr-backend-<agentname>:latest
podman push <acr_name>.azurecr.io/pdr-backend-<agentname>:latest
```

The tag command is used to assign a new tag to your image. This is necessary because ACR requires a specific naming convention. After tagging the image, the `push` command is used to upload the image to the registry.

### Running the image on Azure Container Instances (ACI)

Finally, you can run your image as a container on ACI. Make sure to replace `<acr_name>` with the actual name of your ACR.

Create a container instance with 1 core and 1Gb of memory by running the following command:

[Click here to view the documentation for `az container create`](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az-container-create)

```bash
az container create --resource-group <resource-group-name> --name <container-instance-name> --image <acr-name>.azurecr.io/pdr-backend-<agentname>:latest --cpu 1 --memory 1
```

- --name: The name of the container instance. You will need it in the next step.
- --resource-group: The name of the resource group where you want to create the ACR. You can learn more about managing resource groups from [Azure's documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal).
- --image: The tag of the container image you've pushed to the registry in the previous step.

> **Note**
> You can set the enviroment variables defined in [Configure Enviroment Variables](#configure-environment-variables) step by passing a `--environment-variables <env-variables>` parameter to the `az container create` command.

Please see the [documentation](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az-container-create) to learn about all available commands.

### Monitoring the logs

To monitor the logs of your container, you can use `az container logs` command:

[Click here to view the documentation for `az container logs`](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az-container-logs)

```bash
az container logs --resource-group <resource-group-name> --name <container-instance-name>
```

### More

To access the list of available commands and detailed documentation, you can visit the [Azure documentation page for `az container`](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest). Alternatively, you can use the Azure Portal, which provides a GUI for managing your container instances. Through the portal you can easily perform tasks such as creating new instances, starting and stopping containers, scaling them etc.