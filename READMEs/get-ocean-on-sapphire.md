# Get OCEAN on Sapphire Mainnet

OCEAN has address [`0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520`](https://explorer.oasis.io/mainnet/sapphire/token/0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520) on Sapphire.

There are two approaches to acquire it:

1. Use an OCEAN-ROSE DEX on Sapphire
2. Bridge OCEAN from Eth mainnet

(1) is much simpler. (2) isn't subject to slippage. We cover both below.

# Approach 1: OCEAN-ROSE DEX on Sapphire

How to use:

1. Go to **[Illuminex OCEAN-ROSE pool](https://illuminex.xyz/swap?inputCurrency=0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520&inputChainId=23294&outputCurrency=0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3&outputChainId=23294)**.
2. Specify amount to send, and destination address
3. Click "Swap"

Notes:

- If you see a "Insufficient liquidity" warning, then click the settings gear and toggle "Use secure router = on".
- Be careful for slippage, always. (Though there _should_ be decent liquidity. [Pool info](https://illuminex.xyz/pools/0x841dd137A2B380DA4568f6745aEAc20EDa910313))

# Approach 2: Bridge OCEAN from Eth mainnet

**This approach has three steps:**

1. [Get OCEAN on Eth Mainnet](#1-get-ocean-on-eth-mainnet)
1. [Transfer OCEAN to Sapphire Mainnet via Celer](#2-transfer-ocean-to-sapphire-mainnet-via-celer)
1. [Verify Your Tokens on Sapphire Mainnet](#3-verify-your-tokens-on-sapphire-mainnet)

## A2:1 Get OCEAN on Eth Mainnet

**First, create a Wallet.** For optimal support and the ability to transfer ROSE between paratimes, we recommend the Oasis Wallet extension for Chrome. To proceed, [follow instructions in its docs](https://docs.oasis.io/general/manage-tokens/oasis-wallets/browser-extension/#install-the-oasis-wallet-via-chrome-web-store).

**Then, purchase OCEAN.** First, acquire OCEAN at an exchange like Binance, Coinbase, Gate.io, or KuCoin. Then, withdraw that OCEAN to your web3 wallet.

⚠️ Sending to the wrong address or network will likely result in the loss of your tokens. To minimize risk: send a small test amount first, and double-check the receiving address and network.

## A2:2 Transfer OCEAN to Sapphire Mainnet via Celer

**First, Navigate to Celer bridge.** [Here](https://cbridge.celer.network/1/23294/OCEAN).

**Then, Connect Your Wallet.** Click on the "Connect Wallet" button. Follow the prompts to select and connect your web3 wallet.

**Then, Configure Transfer Settings:**

- Ensure the "From" field is set to "Ethereum Mainnet."
- Confirm "Oasis Sapphire" is selected as the destination on the "To" field.
- Input the amount of OCEAN you desire to transfer in the designated field.

**Finally, Execute the Transfer:**

- Click on the "Transfer" button.
- Review the transaction details.
- Confirm the transaction from your wallet.

## A2:3 Verify Your Tokens on Sapphire Mainnet

Bridging requires several minutes to complete. Your OCEAN will be sent to the address you executed the transaction from.

To verify:

- See the tx on [Oasis Explorer](https://explorer.sapphire.oasis.io/address/0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520/transactions).
- Or, import the OCEAN token contract address `0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520` into your wallet. Set symbol = `OCEAN` and decimal precision = `18`.

Congrats! You've successfully transferred OCEAN to Sapphire Mainnet.

> [!WARNING]
> Disclaimer: This guide does not provide financial advice. Always conduct thorough research or consult a professional before making investment decisions. Make sure to verify URLs and ensure all information aligns with the current operations and networks of the related platforms as cryptocurrency ecosystems frequently update and evolve. Always ensure to use official and secure websites when conducting transactions.
