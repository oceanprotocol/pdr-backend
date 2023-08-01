<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run agents, Locally

In this step, you run and create agents that live on your local machine.

We assume you've already
- (a) [installed pdr-backend](install.md)
- (b) [done local setup](setup-local.md) or [remote setup](setup-remote.md)
- (c) [deployed DT3](deploy-dt3.md)

Steps in this flow:
1. Create agents: trueval, predictoor, trader, ..
2. Run loop with agents interacting

Let's go!

## 1. Create agents

In the same Python console:
```python
import time
from pdr_backend.trueval.trueval import process_block as trueval_process_block
# FIXME: add similar for predictoor, trader, etc
```


## 2. Run loop with agents interacting

This is currently single-threaded. We could make it async & multi-threaded, but that hurts debuggability.

In the same Python console:
```python
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

