# Predictoor Dashboard

**The Predictoor dashboard provides insights into blockchain data through interactive plots and tables.**

## **How it works**

Live data from a specified supported blockchain is fetched and stored in a local database. By running a Dash dashboard, this data is processed and displayed in various formats to provide valuable information and control.

## **How to setup and run**

To set up and run the Predictoor dashboard, follow these steps:

1. **Fetch chain data into the lake**

The first step is to fetch the data from the blockchain using the lake's ETL, by this command:

```console
pdr lake etl update ./my_ppss.yaml sapphire-mainnet
```

For more information on how the lake works and how to configure it, refer to [`this readme`](./lake-and-etl.md).

2. **Run the dash app from command line**

After fetching the chain data locally into the lake, the next step is to read, process, and display the data by running the dashboard with the following command:

```console
pdr dashboard ./my_ppss.yaml sapphire-mainnet
```

This command will open a browser window where you can select predictors and feeds to visualize their performance.

## **How to use**

By default, the plots will be empty because no predictors or feeds are selected.

After **selecting one or more predictors and feeds combinations** where predictions has been submitted, and the payout method called, the plots will be populated with the relevant data.

You can then observe how your predictor bots or others have been performing on different feeds and even compare them.

**IMPORTANT: Only predictions data where the payout method has been called are visible.**

The displayed charts are:

1. **Accuracy** - how predictoor accuracy has evolved durring the selected period of time.
2. **Profit** - what is the profit in OCEAN over the period. Here you can clearly see if you are profitable or not.
3. **Costs** - how much predictoor has staked for each epoch.

## **How to contribute**

We are constantly looking for ways to improve the Predictoor dashboard to help predictors become more profitable and are open to suggestions and ideas.

If you are a predictor and want to help us improve this tool, [join our Discord channel](https://discord.gg/Tvqd7Z648H) and drop a message, or open a GitHub issue.

