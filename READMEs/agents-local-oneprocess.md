<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run local agents, one process for all agents

### Overview

In this step, you run and create agents.

In this README:
- agents live on your local machine
- all agents are on a _single_ process

This is the easiest setup for debugging.

> [!NOTE]
> If you would like to run agents in a container, simply follow the steps outlined in [Running on Docker](./docker.md).

Prerequisites:
- [Installed pdr-backend](install.md)
- [Setup local chain](setup-local.md) or [remote chain](setup-remote.md)
- [Deployed DT3](deploy-dt3.md)

In console:
```console
python
```

### Step: Create & run agents in a single process

In Python console:
```python
import time
from pdr_backend.trueval.trueval import process_block as trueval_process_block
# FIXME: add similar for predictoor, trader, etc

print("Starting main loop...")
trueval_lastblock = 0
while True:
    # trueval agent
    trueval_block = web3_config.w3.eth.block_number
    if block > lastblock:
        trueval_lastblock = trueval_block
        trueval_process_block(web3_config.w3.eth.get_block(trueval_block, full_transactions=False))
    else:
        time.sleep(1)
    # FIXME: add similar for predictoor, trader, etc
```
