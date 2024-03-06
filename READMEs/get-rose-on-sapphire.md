# Get ROSE on Sapphire Mainnet

Steps:

1. [Install Oasis wallet](#1-install-oasis-wallet)
2. [Purchase ROSE](#2-purchase-rose)
3. [Prepare Sapphire EVM account](#3-prepare-sapphire-evm-account)
4. [Transfer ROSE from Oasis Account to Sapphire](#4-transfer-rose-from-oasis-account-to-sapphire)

Bonus: [Sapphire \* Metamask](#5-bonus-sapphire-evm-account-in-metamask)

## 1. Install Oasis Wallet

First, some background:

- **ParaTimes.** "ParaTimes" are subnets in the Oasis chain ecosystem, all reporting to the same "consensus layer". Sapphire, Cipher, and Emerald are Oasis ParaTimes. Each ParaTime has its own independent state. So, ROSE held at the consensus layer is not the same as in Sapphire. But you can swap between them via "deposits" and "withdrawals" in the Oasis wallet.
- **Sapphire.** Each ParaTime has its own specialty. Sapphire's specialty is EVM-compatibility & confidentiality. So, it uses EVM accounts, versus Oasis-native accounts (starts with "0x" vs with "oasis").
- **EVM accounts.** EVM = Ethereum Virtual Machine. EVM-compatible means that it runs Ethereum-style contracts. EVM accounts = Ethereum-style accounts, including an address that starts with "0x" and support for ERC20 tokens.

The **Oasis wallet extension (for Chrome) is the best wallet to transfer ROSE among ParaTimes.** (Metamask is good for pure EVM work in Sapphire. We'll work with that later.)

To install it, go to [Oasis Wallet extension docs](https://docs.oasis.io/general/manage-tokens/oasis-wallets/browser-extension/#install-the-oasis-wallet-via-chrome-web-store) and follow its instructions.

## 2. Purchase ROSE

First, acquire ROSE at an exchange like Binance, Coinbase, Gate.io, or KuCoin. For a full list, see [CoinGecko Oasis page](https://www.coingecko.com/en/coins/oasis-network) -> "Markets" section.

Then, you'll be withdrawing ROSE to your web3 wallet.

- If the exchange supports withdrawal directly to Oasis Sapphire Paratime: great, do that directly! Then you can skip step 3.
- It it doesn't support direct: first, send to Oasis Emerald Network. Then, follow step 3.

⚠️ Sending to the wrong address or network will likely result in the loss of your tokens. To minimize risk: send a small test amount first, and double-check the receiving address and network.

## 3. Prepare Sapphire EVM account

First, make sure you have an EVM account ready for use in Sapphire: you have an EVM address, and you know its private key.

Then, import it into the Oasis wallet extension:

1. Click "Import" button
2. Select "Ethereum-compatible Private Key"
3. Enter account name - whatever you like; click ok
4. Now you will see your new account listed, in the "Ethereum-compatible Account" subsection

Now, let's check your EVM wallet's ROSE balance, via the Oasis wallet extension.

1. There's a circle on the top-right corner. Click it. Now it shows all your Oasis-native _and_ EVM-native accounts.
2. Select your EVM account by clicking on it. Now it has a green check next to it.
3. On the app's very top-left (you may need to scroll), click the left-pointing arrow. Now it shows your EVM account's summary.
4. Click "ParaTimes". Now it shows ROSE balance in each ParaTime for each. Note that your Sapphire account has 0.0 ROSE.

## 4. Transfer ROSE from Oasis Account to Sapphire

Here, we use the Oasis wallet extension to transfer ROSE from your Oasis-native account to your EVM Sapphire account.

1. Go to the "ParaTimes" section
2. In the "Sapphire" box, click on "To ParaTime"
3. In the "Amount" field, specify the # ROSE; in the "To" field, enter your EVM account address (0x...).
4. Click "Next". Click to confirm.
5. The wallet will show an animation; then it will say "submitted"; then it will say "Successful" and share tx details.

To verify that the tx went through:

- Verify "withdraw" side: in Oasis wallet, in the Oasis account you sent from, in its tx history, click on the most recent tx. Copy the the txHash value. Finally, go to [oasisscan.com](https://www.oasisscan.com/) and paste in the txHash value.
- But note that its "to" address is an oasis address, _not_ your EVM address. This address is the middleman bridge from your Oasis-native sending account to your EVM-native receiving account. So we still need to verify the "deposit" side, in the EVM account.
- Verify "deposit" side: via the Oasis wallet extension, check your EVM wallet's balance as described above). The balance should have increased by the amount of ROSE that you sent.

The official Oasis guide has details: [How to Transfer ROSE into a ParaTime](https://docs.oasis.io/general/manage-tokens/how-to-transfer-rose-into-paratime)

## 5. Bonus: Sapphire EVM Account in Metamask

Metamask supports Sapphire EVM. Here's how to use it.

To add Sapphire network:

1. Go to `https://docs.oasis.io/dapp/sapphire/`.
2. In that page click "click here to register Sapphire Mainnet on Metamask".
3. Confirm the prompts to switch to Sapphire network

To add your Sapphire EVM account:

1. In Metamask, in top middle "account" subsection, click the dropdown
2. Click "Add account or hardware wallet". Follow the prompt.

To see your ROSE balance:

1. In Metamask, click "Tokens"
2. Observe the ROSE balance.

> [!WARNING]
> Disclaimer: This guide does not provide financial advice. Always conduct thorough research or consult a professional before making investment decisions. Make sure to verify URLs and ensure all information aligns with the current operations and networks of the related platforms as cryptocurrency ecosystems frequently update and evolve. Always ensure to use official and secure websites when conducting transactions.
