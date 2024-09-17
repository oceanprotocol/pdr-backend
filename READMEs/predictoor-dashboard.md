# Predictoor Dashboard

**The Predictoor dashboard provides insights into blockchain data through interactive plots and tables.**

## **How it works**

Live data from a specified supported blockchain is fetched and stored in a local database. By running a Dash dashboard, this data is processed and displayed in various formats to provide valuable information and control.

## **How to setup and run**

To set up and run the Predictoor dashboard, follow these steps:

1. **Fetch chain data into the lake and export to paruqet files**

The first step is to fetch the data from the blockchain using the lake's ETL, by this command:

```console
pdr lake etl update ./my_ppss.yaml sapphire-mainnet
```

By default the lake is going to automatically export data from lake to parquet files.
Be aware that the export is executed periodically and could be configured and even disabled using this PPSS lake config params:
- export_db_data_to_parquet_files
- seconds_between_parquet_exports
- number_of_files_after_which_re_export_db

For more information on how the lake works and how to configure it, refer to [`this readme`](./lake-and-etl.md).

2. **Configure ppss(Optional)**

This step is optional but very useful and **highly recommended if you are running a Predictoor bot**.

By configuring the **ppss -> predictoor_ss -> my_addresses** list and providing one or multiple predictoor addresses, you can easily track those addresses. The app will automatically read the addresses and display all relevant data when it starts. Additionally, if you modify settings and select different Predictoors and feeds, you can easily reset the dashboard to your Predictoor settings.

3. **Run the dash app from command line**

After fetching the chain data locally into the lake and exporting it into parquet files, the next step is to read, process, and display the data by running the dashboard with the following command:

```console
pdr dashboard ./my_ppss.yaml sapphire-mainnet
```

This command will open a browser window where you can select predictoors and feeds to visualize their performance.

## **How to use**

By default, if ppss is not configured with predictoor addresses, the plots will be empty until at least one predictoor and feed are selected. Otherwise you will see stats on the provided predictoor addresses.

After **selecting one or more predictors and feeds combinations** where predictions has been submitted, and the payout method called, the plots and metrics will be populated with the relevant data.

You can then observe how your predictoor bots or others have been performing on different feeds and even compare them.

**IMPORTANT: Only predictions data where the payout method has been called are visible.**

The displayed charts are:
1. **Accuracy** - how predictoor accuracy has evolved durring the selected period of time.
2. **Profit** - what is the profit in OCEAN over the period. Here you can clearly see if you are profitable or not.
3. **Costs** - how much predictoor has staked for each epoch.


To summarize the stats across multiple feeds and Predictoors, follow the **displayed metrics**. These include: **Average Accuracy, Total Profit, and Average Stake**. These metrics make it easy to track overall statistics for the selected Predictoors and users.


Furthermore, you can select different periods of time for the data calculation, so you can easily see stats on **last day, last week, or last month**.

## **How to contribute**

We are constantly looking for ways to improve the Predictoor dashboard to help predictoors become more profitable and are open to suggestions and ideas.

If you are a predictoor and want to help us improve this tool, [join our Discord channel](https://discord.gg/Tvqd7Z648H) and drop a message, or open a GitHub issue.

