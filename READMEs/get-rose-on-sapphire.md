# Get ROSE on Sapphire Mainnet

Steps:

1. [Create a Wallet](#1-create-a-wallet)
2. [Purchase ROSE](#2-purchase-rose)
3. [Transfer ROSE from Oasis Wallet to Sapphire](#3-transfer-rose-from-oasis-wallet-to-sapphire)

## 1. Create a Wallet

For optimal support and the ability to transfer ROSE between paratimes, we recommended to use Oasis Wallet extension for Chrome.

To install, go to [Oasis Wallet extension documentation](https://docs.oasis.io/general/manage-tokens/oasis-wallets/browser-extension/#install-the-oasis-wallet-via-chrome-web-store) and follow its instructions.

## 2. Purchase ROSE

First, acquire ROSE at an exchange like Binance, Coinbase, Gate.io, or KuCoin. For a full list, see [Coingecko Oasis page](https://www.coingecko.com/en/coins/oasis-network) -> "Markets" section.

Then, you'll be withdrawing ROSE to your web3 wallet.
- If the exchange supports withdrawal directly to Oasis Sapphire Paratime: great, do that directly! Then you can skip step 3. 
- It it doesn't support direct: first, send to Oasis Emerald Network. Then, follow step 3.

⚠️ Sending to the wrong address or network will likely result in the loss of your tokens. To minimize risk: send a small test amount first, and double-check the receiving address and network.

## 3. Transfer ROSE from Oasis wallet to Sapphire

"ParaTimes" are subnets in the Oasis chain ecosystem. Sapphire is a ParaTime. Sapphire is EVM-compatible, which means that it supports EVM accounts. In fact, each Sapphire account is a pair of (EVM account, Oasis-native accounts).

About "EVM" accounts: EVM = Ethereum Virtual Machine. EVM-compatible means that it runs Ethereum-style contracts. EVM accounts = Ethereum-style accounts, including an address that starts with "0x" and support for ERC20 tokens.

Whereas EVM wallets start with "0x", Oasis-native wallets start with "oasis". Therefore it's easy to distinguish them.

**Prepare EVM account**
Let's make sure you have EVM account ready for use in Sapphire. That is, you have an EVM address, and you know its private key. 

Optionally, you can import it into the Oasis wallet extension, such that you can check its balances before and after. To do so, in the extension:
1. Click "Import" button
2. Select "Ethereum-compatible Private Key"
3. Enter account name (this can be arbitrary). Click ok
4. Now you will see your new account listed with other accounts, in the "Ethereum-compatible Account" subsetion

**Transfer the ROSE to your (EVM) Sapphire account, using the Oasis wallet extension:**
1. Go to the "ParaTimes" section
2. In the "Sapphire" box, click on "To ParaTime"
3. In the "Amount" field, specify the # ROSE; in the "To" field, enter your EVM account address (0x...).
4. Click "Next". Click to confirm.
5. The wallet will show an animation; then it will say "submitted"; then it will say "Successful" and share tx details. To further verify: click on "View transactions through explorer". Note that the "to" address is the Oasis-native address, not the EVM one; that's fine.

The official Oasis guide has details: [How to Transfer ROSE into a ParaTime](https://docs.oasis.io/general/manage-tokens/how-to-transfer-rose-into-paratime)

⚠️ Be sure to select “Sapphire” as the destination ParaTime during the transfer process. Double-check this selection to avoid transferring tokens to an unintended ParaTime. 

## Conclusion

Congratulations! You have successfully transferred ROSE to Sapphire Mainnet. Do manage private keys with utmost care.


> [!WARNING]
> Disclaimer: This guide does not provide financial advice. Always conduct thorough research or consult a professional before making investment decisions. Make sure to verify URLs and ensure all information aligns with the current operations and networks of the related platforms as cryptocurrency ecosystems frequently update and evolve. Always ensure to use official and secure websites when conducting transactions.
