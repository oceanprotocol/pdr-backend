# Run Remote Predictoor/Trader Bot, Remote Network

This README describes:
- Running a *remote predictoor or trader* bot (agent), on Azure
- On a *remote network* where other bots are remote
- It uses containers

You will build a container, upload it to Azure Container Registry, and finally run it using Azure Container Instances.

This example uses Sapphire testnet; you can modify envvars to run on Sapphire mainnet.


**Steps:**

1. Setup
    - [Get tokens](#get-tokens)
    - [Pre-requisites](#pre-requisites)
    - [Install bot](#install)
2. [Build a container image](#build-a-container-image)
2. [Setup & run bot on Azure](#run-bot-on-azure)
    - [Install Azure CLI](#install-azure-cli)
    - [Build a container image of bot](#build-container-image)
    - [Setup ACR](#setup-acr) (Azure Container Registry)
    - [Push image to ACR](#push-image-to-acr)
    - [Run image on ACI](#run-image-on-azure-aci) (Azure Container Instances)
    - [Monitor container logs](#monitor-container-logs)
3. Appendix
    - [Further Azure Resources](#further-azure-resources)
    - [Other Deployment Venues](#other-deployment-venues)

> **Warning**
> These docs are up-to-date as of August 2023. If you encounter any issues or need the latest instructions, please see [Azure docs](https://learn.microsoft.com/en-us/azure/app-service/tutorial-custom-container?tabs=azure-cli&pivots=container-linux) on running containers.

### Get Tokens

[See get-tokens.md](./get-tokens.md).

### Pre-Requisites

The actions in this README require Docker or Podman to be installed.

### Install Bot

The predictoor/trader bots run code that lives in `pdr-backend` repo.

[Install pdr-backend](install.md).


## Build a Container Image

Here, we will build a container image for your bot.

In console, in the root directory of your repo, run:
```console
# if docker
docker build -t pdr-backend-<botname>:latest .

# if podman
podman build -t pdr-backend-<botname>:latest .
```

Where `botname` = the name of your bot.

This command builds a container image using the Dockerfile in the current directory and tag it as `pdr-backend-<botname>:latest`. You can use any tag you'd like.


## Run Bot on Azure

Here, we run the bot on Azure. (The Appendix lists other venues.)

### Install Azure CLI

Follow the instructions from [Microsoft's website](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli#install) to install. Then type `az login` in the terminal to log-in.

### Setup ACR

Next, create an Azure Container Registry (ACR) where you'll upload your container image.

[Click here to view the documentation for `az acr create`](https://learn.microsoft.com/en-us/cli/azure/acr?view=azure-cli-latest#az-acr-create)

```console
az acr create --name <ACR_NAME> --resource-group <resource group name> --sku <sku>
```

Where:
- `--name`: The name of the container registry. It should be specified in lower case. You will need it in the next step.
- `--resource-group`: The name of the resource group where you want to create the ACR. You can learn more about managing resource groups from [Azure's documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal).
- `--sku`: Pricing tier for ACR, accepted values are: `Basic`, `Standard`, `Premium`.

### Push image to ACR

You can now push your container image to ACR. Don't forget to replace `<acr_name>` with the name you gave to your ACR in the previous step.

Firstly, you'll need to provide docker or podman with access to your ACR.

[Click here to view the documentation for `az acr login`](https://learn.microsoft.com/en-us/cli/azure/acr?view=azure-cli-latest#az-acr-login)

```console
az acr login --name <acr_name>
```

> **Note**
> If you need to get access token you can use `--expose-token` parameter and login using `podman/docker login` command.

Push the container image to the registry.

```console
# docker
docker tag pdr-backend-<botname>:latest <acr_name>.azurecr.io/pdr-backend-<botname>:latest
docker push <acr_name>.azurecr.io/pdr-backend-<botname>:latest
```

```console
# podman
podman tag pdr-backend-<botname>:latest <acr_name>.azurecr.io/pdr-backend-<botname>:latest
podman push <acr_name>.azurecr.io/pdr-backend-<botname>:latest
```

The tag command is used to assign a new tag to your image. This is necessary because ACR requires a specific naming convention. After tagging the image, the `push` command is used to upload the image to the registry.

### Run Image on ACI

Finally, you can run your image as a container on Azure Container Instances (ACI). Make sure to replace `<acr_name>` with the actual name of your ACR.

To create a container instance with 1 core and 1Gb of memory: in console:
```console
az container create --resource-group <resource-group-name> --name <container-instance-name> --image <acr-name>.azurecr.io/pdr-backend-<botname>:latest --cpu 1 --memory 1
```

Where:
- `--name`: The name of the container instance. You will need it in the next step.
- `--resource-group`: The name of the resource group where you want to create the ACR. You can learn more about managing resource groups from [Azure's documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal).
- `--image`: The tag of the container image you've pushed to the registry in the previous step.

> **Note**
> You can set envvars defined in [Configure Enviroment Variables](#configure-environment-variables) step by passing `--environment-variables <env-variables>` parameter to the `az container create` command.

([Azure docs](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az-container-create) have more details.)

### Monitor container logs

In console:
```console
az container logs --resource-group <resource-group-name> --name <container-instance-name>
```

([Azure docs](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az-container-logs) have more details.)

## Appendix

### Further Azure Resources

The [Azure docs](https://learn.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest) have more details, including on CLI commands.

You can also use the Azure Portal. It's a GUI to manage your container instances. Through it, you can create new instances, start & stop containers, scale them, and more.


### Other Deployment Venues

Above, we focused on Azure. Here are several deployment options:

- [Azure - Azure Container Instances (ACI)](#running-on-azure-as-a-container)
- [Heroku - Container Registry & Runtime (Docker Deploys)](https://devcenter.heroku.com/articles/container-registry-and-runtime)
- [AWS -  Deploy Docker Containers on Amazon ECS](https://aws.amazon.com/getting-started/hands-on/deploy-docker-containers/)
- [Google Cloud - Deploying to Cloud Run](https://cloud.google.com/run/docs/deploying)

## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Parent trader README: trader.md](./trader.md)
- [Root README](../README.md)