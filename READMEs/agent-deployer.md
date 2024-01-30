# Agent Deployment Tool

`deployer` is a streamlined command-line utility designed for efficiently generating and managing Predictoor agent deployments.

## Usage

### Agent Configurations
Firstly, you need to set up your agents configuration. This is done by creating a config entry under `deployment_configs` in `ppss.yaml` file. 

Here is an example structure for your reference:

```yaml
deployment_configs:
  testnet_predictoor_deployment:
    cpu: '1' # k8s
    memory: '512Mi' # k8s
    source: "binance"
    type: "predictoor"
    approach: 3
    network: "sapphire-testnet"
    s_until_epoch_end: 20
    pdr_backend_image_source: "oceanprotocol/pdr-backend:latest" # docker-compose and k8s
    agents:
      - pair: 'BTC/USDT'
        stake_amt: 15
        timeframe: 5m
        approach: 1
      - pair: 'ETH/USDT'
        stake_amt: 20
        timeframe: 1h
        s_until_epoch_end: 60
```

*Tip: Specific agent settings (like source, timeframe) will override general settings if provided.*

### Private Keys

Create a `.keys.json` file and format it as follows:
```
{
    "config_name": ["pk1", "pk2"...]
}
```

*Note: If you have fewer private keys than number of agents, the tool will create new wallets and update the .keys.json file.*

### Generate Templates

The `generate` command is used to create deployment template files based on a configuration file.

```
pdr deployer generate <config_path> <config_name> <deployment_method> <output_dir>
```

- `<config_path>`: Path to the yaml config file.
- `<config_name>`: Name of the config.
- `<deployment_method>`: Method of deployment (choices: "k8s").
- `<output_dir>`: Output directory for the generated files.

Take a note of the `config_name`, you will need it later!

### Deploy Config

The `deploy` command is used to deploy agents based on a specified config name.

```
pdr deployer deploy <config_name> [-p PROVIDER] [-r REGION] [--project_id PROJECT_ID] [--resource_group RESOURCE_GROUP] [--subscription_id SUBSCRIPTION_ID]
```

- `<config_name>`: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)
- -r, --region: Deployment zone/region (optional).
- --project_id: Google Cloud project id (optional).
- --resource_group: Azure resource group (optional).
- --subscription_id: Azure subscription id (optional).

### Destroy Config

The `destroy` command is used to destroy agents deployed based on a specified configuration.

```
pdr deployer destroy <config_name> [-p PROVIDER]
```

- `<config_name>`: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)

### Logs

The `logs` command is used to retrieve logs from deployed agents.

```
pdr deployer logs <config_name> [-p PROVIDER]
```

- `<config_name>`: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)


### Remote Container Registry

The `registry` command is used to manage remote registries for agent deployment.

```
pdr deployer registry <action> <registry_name> [-p PROVIDER] [-r REGION] [--project_id PROJECT_ID] [--resource_group RESOURCE_GROUP]
```

- `<action>`: Action (choices: "deploy", "destroy", "auth", "url").
- `<registry_name>`: Registry name.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp").
- -r, --region: Deployment zone/region (optional).
- --project_id: Google Cloud project id (optional).
- --resource_group: Azure resource group (optional).


### Build

The build command is used to build a container image.

```
pdr deployer build <image_name> <image_tag>
```

- `<image_name>`: Image name (default: "pdr_backend").
- `<image_tag>`: Image tag (default: "deployer").


#### Push

The `push` command is used to push container images to a remote registry.

```
pdr deployer push <registry_name> [<image_name>] [<image_tag>]
```

- `<registry_name>`: Registry name.
- `<image_name>`: Image name (default: "pdr_backend").
- `<image_tag>`: Image tag (default: "deployer").


## Examples

### K8S with GCP

Outputs are truncated for brevity.

```shell
$ pdr deployer generate ppss.yaml predictoors_cluster k8s ./predictoors_approach3
Generated k8s templates for predictoors_cluster
  Output path: ./predictoor_approach3
  Config name: predictoors_cluster
  Deployment method: k8s
  Number of agents: 2
To deploy: pdr deployer deploy predictoors_cluster
```

```shell
$ pdr deployer deploy predictoors_cluster -p gcp -r europe-west2 --project_id id_goes_here
Deploying predictoors_cluster...
Authenticating to Kubernetes cluster...
Fetching cluster endpoint and auth data.
kubeconfig entry generated for predictoors_cluster.
Cluster is ready, deploying the agents...
namespace/predictoors_cluster created
deployment.apps/pdr-predictoor1-3-btc-usdt-5m-binance created
deployment.apps/pdr-predictoor2-3-eth-usdt-5m-binance created
```

```shell
$ pdr deployer logs predictoors_cluster
Getting logs for predictoors_cluster...
Getting cluster logs...
NAME                                                     READY   STATUS    RESTARTS   AGE
pdr-predictoor1-3-btc-usdt-5m-binance-1294c5aa3-fjc65    1/1     Running   0          91s
pdr-predictoor2-3-eth-usdt-5m-binance-21dfcf3bc4-b6nnk   1/1     Running   0          91s
-> Submit predict tx result: success.
====================================================================================================================================================================================
cur_epoch=5688716, cur_block_number=4658908, cur_timestamp=1706615099, next_slot=1706615100, target_slot=1706615400. 295 s left in epoch (predict if <= 30 s left). s_per_epoch=300
...
```