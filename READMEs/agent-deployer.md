# Agent Deployment Tool

Agent Deployment Tool is a streamlined command-line utility designed for efficiently generating and managing Predictoor agent deployments.

## Usage

#### Agent Configurations
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

#### Private Keys

Create a `.keys.json` file and format it as follows:
```
{
    "config_name": ["pk1", "pk2"...]
}
```

*Note: If you have fewer private keys than number of agents, the tool will create new wallets and update the .keys.json file.*

#### Generate Templates

The `generate` command is used to create deployment template files based on a configuration file.

```
pdr deployer generate <config_path> <config_name> <deployment_method> <output_dir>
```

- <config_path>: Path to the yaml config file.
- <config_name>: Name of the config.
- <deployment_method>: Method of deployment (choices: "k8s", "pm2", "docker-compose").
- <output_dir>: Output directory for the generated files.

Take a note of the `config_name`, you will need it later!

#### Deploy Config

The `deploy` command is used to deploy agents based on a specified config name.

```
pdr deployer deploy <config_name> [-p PROVIDER] [-r REGION] [--project_id PROJECT_ID] [--resource_group RESOURCE_GROUP]
```

- <config_name>: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)
- -r, --region: Deployment zone/region (optional).
- --project_id: Google Cloud project id (optional).
- --resource_group: Azure resource group (optional).

#### Destroy Config

The `destroy` command is used to destroy agents deployed based on a specified configuration.

```
pdr deployer destroy <config_name> [-p PROVIDER]
```

- <config_name>: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)

#### Logs

The `logs` command is used to retrieve logs from deployed agents.

```
pdr deployer logs <config_name> [-p PROVIDER]
```

- <config_name>: Name of the config.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp"). (optional)


#### Remote Container Registry

The `registry` command is used to manage remote registries for agent deployment.

```
pdr deployer registry <action> <registry_name> [-p PROVIDER] [-r REGION] [--project_id PROJECT_ID] [--resource_group RESOURCE_GROUP]
```

- <action>: Action (choices: "deploy", "destroy", "auth", "url").
- <registry_name>: Registry name.
- -p, --provider: Cloud provider (optional, choices: "aws", "azure", "gcp").
- -r, --region: Deployment zone/region (optional).
- --project_id: Google Cloud project id (optional).
- --resource_group: Azure resource group (optional).


#### Build

The build command is used to build a container image.

```
pdr deployer build <image_name> <image_tag>
```

- <image_name>: Image name (default: "pdr_backend").
- <image_tag>: Image tag (default: "deployer").


#### Push

The `push` command is used to push container images to a remote registry.

```
pdr deployer push <registry_name> [<image_name>] [<image_tag>]
```

- <registry_name>: Registry name.
- <image_name>: Image name (default: "pdr_backend").
- <image_tag>: Image tag (default: "deployer").


**Example:**

```shell
$ pdr deployer generate ppss.yaml testnet_predictoor_deployment pm2 ./pm2dir
Generated pm2 templates for testnet_predictoor_deployment
  Output path: ./pm2dir
  Config name: testnet_predictoor_deployment
  Deployment method: pm2
  Number of agents: 2
Run command: pdr deployer deploy testnet_predictoor_deployment
$ pdr deployer deploy testnet_predictoor_deployment
┌────┬──────────────────────────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id │ name                                     │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├────┼──────────────────────────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0  │ pdr-predictoor1-1-BTC/USDT-5m-binance    │ default     │ N/A     │ fork    │ 72470    │ 0s     │ 0    │ online    │ 0%       │ 7.6mb    │ user   │ disabled │
│ 1  │ pdr-predictoor2-3-ETH/USDT-1h-binance    │ default     │ N/A     │ fork    │ 72471    │ 0s     │ 0    │ online    │ 0%       │ 5.0mb    │ user   │ disabled │

$ pdr deployer logs testnet_predictoor_deployment
....

$ pdr deployer destroy testnet_predictoor_deployment
....
```