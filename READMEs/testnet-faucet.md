# Get fake tokens on Oasis Sapphire testnet

This README describes how to:
- [Get fake ROSE on Sapphire testnet](#get-fake-rose-on-sapphire-testnet)
- [Get fake OCEAN on Sapphire testnet](#get-fake-ocean-on-sapphire-testnet)

If you need, [create a new EVM account](#create-new-evm-account) first.

## Get fake ROSE on Sapphire testnet

1. Go to [ROSE faucet for Oasis testnets](https://faucet.testnet.oasis.dev/).
2. From the dropdown, pick `Sapphire` testnet.
3. Fill in your address and request test tokens.

## Get fake OCEAN on Sapphire testnet

1. Go to the [OCEAN faucet for Sapphire testnet](https://faucet.sapphire.oceanprotocol.com/).
2. Fill in your address and click `Get 1000 OCEAN`.
3. (Optional) in your wallet, add the OCEAN token. If needed, specify the OCEAN address as: 0x973e69303259B0c2543a38665122b773D28405fB

## Create new EVM account

Oasis Sapphire testnet is an EVM-based chain. An EVM account is singularly defined by its private key. Its address is a function of that key. Let's generate an account!

First, run Python. In a console:
```console
python
```

In the Python console:
```python
from eth_account.account import Account
account = Account.create()

print(f"PRIVATE_KEY={account.key.hex()}, ADDRESS={account.address}")
```

Now, you have an EVM account: address & private key. Save the values somewhere safe, like a local file or a password manager.

These accounts will work on Sapphire testnet, Sapphire mainnet, Eth mainnet, or any other EVM-based chain.

## Get address from private key

In the Python console:
```python
from eth_account.account import Account
private_key = <your private key>
account = Account.from_key(private_key)

print(f"PRIVATE_KEY={account.key.hex()}, ADDRESS={account.address}")
```
