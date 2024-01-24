# Agent Deployment Tool

Agent Deployment Tool is a streamlined command-line utility designed for efficiently generating and managing Predictoor agent deployments.

## Usage

### Step 1. Generate Deployment Templates

#### Agent Configurations
Firstly, you need to set up your agents configuration. This is done by creating a `config.yaml` file.

Here is an example structure for your reference:

```yaml
predictoor_config:
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

Run the following command to create the deployment template files:

```
deployer generate <config_path> <config_name> <deployment_method> <output_dir>
```

**Example:**

```shell
$ python agent-deploy/deployer.py generate agent-deploy/config.yaml predictoor_config pm2 ./pm2dir
Generated pm2 templates for predictoor_config
  Output path: ./pm2dir
  Config name: predictoor_config
  Deployment method: pm2
  Number of agents: 2
Run command: pm2 start ./pm2dir/*.js
$ pm2 start ./pm2dir/*.js
┌────┬──────────────────────────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id │ name                                     │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├────┼──────────────────────────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0  │ pdr-predictoor1-1-BTC/USDT-5m-binance    │ default     │ N/A     │ fork    │ 72470    │ 0s     │ 0    │ online    │ 0%       │ 7.6mb    │ user   │ disabled │
│ 1  │ pdr-predictoor2-3-ETH/USDT-1h-binance    │ default     │ N/A     │ fork    │ 72471    │ 0s     │ 0    │ online    │ 0%       │ 5.0mb    │ user   │ disabled │
```

## Available Deployment Methods
You can deploy using one of the following methods:
- "k8s"
- "docker-compose"
- "pm2"