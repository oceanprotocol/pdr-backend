<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Remote Setup

**NOTE: THIS IS NOT COMPLETE! It will need heavy revisions to work on Oasis, and proper testing.**

Here, we do setup for Oasis Sapphire testnet (Sapptest). It's similar for Oasis Sapphire mainnet (Sappmain).

We assume you've already [installed pdr-backend](install.md).

For brevity, we refer to 

Here, we will:
1. Create two accounts - `REMOTE_TEST_PRIVATE_KEY1` and `2`
2. Get fake ROSE on Sapptest
3. Get fake OCEAN ""
4. Set envvars
5. Set up Alice and Bob wallets in Python

Let's go!

## 1. Create EVM Accounts (One-Time)

An EVM account is singularly defined by its private key. Its address is a function of that key. Let's generate two accounts!

In a new or existing console, run Python.
```console
python
```

In the Python console:

```python
from eth_account.account import Account
account1 = Account.create()
account2 = Account.create()

print(f"""
REMOTE_TEST_PRIVATE_KEY1={account1.key.hex()}, ADDRESS1={account1.address}
REMOTE_TEST_PRIVATE_KEY2={account2.key.hex()}, ADDRESS2={account2.address}
""")
```

Then, hit Ctrl-C to exit the Python console.

Now, you have two EVM accounts (address & private key). Save them somewhere safe, like a local file or a password manager.

These accounts will work on any EVM-based chain: production chains like Eth mainnet and Polygon, and testnets like Goerli and Sapptest. Here, we'll use them for Sapptest.

## 2. Get (fake) ROSE on Sapptest

We need the network's native token to pay for transactions on the network. ETH is the native token for Ethereum mainnet, ROSE is the native token for Polygon, and (fake) ROSE is the native token for Sapptest.

To get free (fake) ROSE on Sapptest:
1. Go to the faucet (FIXME_URL) Ensure you've selected "Sapptest" network and "ROSE" token.
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported ROSE balance: `FIXME_URL/<ADDRESS1 or ADDRESS2>`

## 3. Get (fake) OCEAN on Sapptest

In Predictoor, OCEAN is used as follows:
- by traders, to purchase data feeds
- by predictoors, for staking on predictions, and for earnings from predictions

- OCEAN is an ERC20 token with a finite supply, rooted in Ethereum mainnet at address [`0x967da4048cD07aB37855c090aAF366e4ce1b9F48`](https://etherscan.io/token/0x967da4048cD07aB37855c090aAF366e4ce1b9F48).
- OCEAN on other production chains derives from the Ethereum mainnet OCEAN. OCEAN on Sappmain [`FIXME_token_address`](FIXME_URL).
- (Fake) OCEAN is on each testnet. Fake OCEAN on Sapptest is at [`FIXME_token_address`](FIXME_URL).

To get free (fake) OCEAN on Sapptest:
1. Go to the faucet FIXME_URL
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported OCEAN balance: `FIXME_URL?a=<ADDRESS1 or ADDRESS2>`

## 4. Set envvars

In your working console:
```console
export REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
export REMOTE_TEST_PRIVATE_KEY2=<your REMOTE_TEST_PRIVATE_KEY2>
```

Check out the [environment variables documentation](./envvars.md) to learn more about the environment variables that could be set.
