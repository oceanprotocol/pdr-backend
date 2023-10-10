<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run a Predictoor Bot

Let's run a predictoor bot (agent), to submit predictions and earn $.

**Steps:**

Start simple, layer in complexity.

1. [Local predictoor, local network](localpredictoor-localnet.md)
2. [Local predictoor, remote network](./localbot-remotenet.md) - on testnet
3. [Remote predictoor, remote network](./remotebot-remotenet.md) - on testnet
4. Repeat (2) or (3), on mainnet

## Requesting payout

Congratulations on your participation and progress in making predictions. Whether you've made accurate or erroneous predictions, it's now time to claim your earnings from correct predictions.

### Recommended Payout Frequency

While you can request a payout at any time, we suggest doing so periodically. The payout module processes requests in batches, handling up to 250 slots per transaction for efficiency.

### Steps to Request Payout

#### Preparation

Ensure you pause or stop any ongoing prediction submissions. This is crucial as active submissions can interfere with the payout process.

#### Execute Payout

- Running locally: Simply run the python script with the command: `python pdr_backend/predictoor/payout.py`.
- Using Container Image: Simply execute the command: `predictoor payout`.

#### Completion

Once the payout module concludes its operation, your balance will reflect the updated amount.

#### Verification

It's good practice to run the payout module again. This ensures any failed blockchain calls from the previous attempt are addressed and verifies that all eligible payouts have been claimed.

## Warning

You will lose money as a predictoor if your $ out exceeds your $ in. If you have low accuracy you’ll have your stake slashed a lot. Do account for gas fees, compute costs, and more. Everything you do is your responsibility, at your discretion. None of this repo is financial advice.
