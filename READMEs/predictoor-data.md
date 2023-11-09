<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Get Predictoor bot performance data

This README presents how to get some data related to the Predictoor bot performance.

Great job on becoming a Predictoor. You should be submitting predictions and claiming some rewards by now.

Next you might want now to see exactly how accurate yout bot is and how much you have earned, let's do it!

### Steps to Get Predictoor Data

#### 1. Preparation

Ensure you have claimed payout at least once before you continue.

#### 2. How to get predictoor data

- Make sure you still have the `RPC_URL` env variable set.

- Run the folowing python script with the command: `python scripts/get_predictoor_info.py WALLET_ADDRESS START_DATE END_DATE NETWORK OUTPUT_DIRECTORY`.

- Used parameters:
    - `WALLET_ADDRESS`: the wallet address used for submitting the predictions.
    - `STARTE_DATE`: format yyyy-mm-dd - the date starting from which to query data.
    - `END_DATE`: format yyyy-mm-dd - the date to query data until.
    - `NETWORK`: mainnet | testnet - the network to get the data from.
    - `OUTPUT_DIRECTORY`: where to create the csv files with the grabbed data.   

#### 3. What is the output

- in console you are going to see the **Accuracy**, **Total Stake**, **Total Payout** and **Number of predictions** for each pair and also the mentioned values over all pairs.

- in the specified output directory: you are going to find generate CSV files with the following file name format: **'{PAIR}{TIMEFRAME}{EXCHANGE}'**, containing: **Predicted Value, True Value, Timestamp, Stake, Payout**




