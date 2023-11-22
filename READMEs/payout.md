<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Claim Payout for Predictoor Bot

This README describes how you can claim the $ based on running a predictoor bot.

First, congratulations on your participation and progress in making predictions! Whether you've made accurate or erroneous predictions, it's now time to claim your earnings from correct predictions.

### Steps to Request Payout

#### 1. Preparation

Ensure you pause or stop any ongoing prediction submissions. You can use `Ctrl-C` to stop the predictions. This is crucial as active submissions can interfere with the payout process.

#### 2. Execute Payout

From console:
```console
pdr claim_OCEAN ppss.yaml
```

#### 3. Completion

Once the payout module concludes its operation, your balance will reflect the updated amount.

#### 4. Verification

It's good practice to run the payout module again. This ensures any failed blockchain calls from the previous attempt are addressed and verifies that all eligible payouts have been claimed.

### Steps to Request ROSE Rewards

#### 1. Preparation
 - Make sure you requested your Payout mentioned above, between the DF round end and ROSE rewards distribution(on Monday, 4 days after the DF round ends), for all your predictions from the DF round to be counted in ROSE rewards calculation.
 - Ensure you pause or stop any ongoing prediction submissions. You can use `Ctrl-C` to stop the predictions. This is crucial as active submissions can interfere with the payout process.

#### 2. Claim ROSE Rewards

From console:
```console
pdr claim_ROSE ppss.yaml
```

#### 3. Completion

Once the claim module concludes its operation, your balance will reflect the updated amount.

#### 4. Verification

It's good practice to run the payout module again. This ensures any failed blockchain calls from the previous attempt are addressed and verifies that all eligible payouts have been claimed.

## FAQ

- Q: how often to request?
- A: While you can request a payout at any time, we suggest doing so periodically. The payout module processes requests in batches, handling up to 250 slots per transaction for efficiency.
