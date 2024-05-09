<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Lake,ETL, and PredictoorJob Overview

This README describes how you can operate the lake and use analytics to understand the world of predictoor.

First, we want to make sure we get all the data we'll need! Then, we'll process this data so it's easy to chart and undeerstand things.

To complete this we'll be interacting different components in our stack, such as the: lake, GQLDataFactory, and the ETL.

## Lake - Think "Database"
For most users, the lake can simply be thought of as a database. It contains many tables with complete records and reliable information. It should be easy to understand and to work with. We use a combination of CSVs & DuckDB as our Data Lake/Warehouse.

Currently, the "Lake" (DB) data can be accessed via the PersistentDataStore (PDS - DuckDB Wrapper) and operated with via the CLI module `lake` command `pdr lake describe ppss.yaml sapphire-mainnet` (cli_module_lake.py)

Some features include:
1. The lake has a few commands: `describe`, `validate`, `update`, `drop`, and `query`
1. The lake is made up of many timeseries objects that should exist from `st_ts` and `end_ts`.
1. All the data inside lake tables should exist between `st_ts` and `end_ts`.
1. The `st_ts` and `end_ts` checkpoints come from `ppss.yaml` but are computed through the lake as time progresses, new events are fired, and records are processed.
1. The lake is designed so raw data is fetched once, so the rest can be rebuilt many times.
1. The main work building the data take place inside the ETL in the form of SQL queries that run on DuckDB.
1. The lake does not support backfilling, you have to drop all data and then set a new ppss.lake_ss.st_ts.

## ETL
Is responsible for running a series of Jobs and queries that keep the lake in great shape.

### ETL - End-To-End Update from CLI
1. from the cli - `pdr lake raw update && pdr lake etl update`

### ETL - End-To-End - Data Workflow from Code
As you are developing and building around the data and lake, you might need to update how the system works, and be able to follow this workflow.
1. GQLDF completes succesfully. Fetch from source raw => into CSV & DuckDB.
1. Run SQL query over this data to clean it, join w/ other tables, transform => into Bronze Tables
1. Aggregating + Summarizing it => into Silver & Gold tables.
1. Serving this data into dahboards and other locations.

### ETL - User Operations Workflow from Code & CLI
As you are developing and building around the lake, your workflow migh look like this.
1. Writing & Updating ETL code
1. Dropping ETL tables via CLI
1. Rebuilding ETL tables via CLI

### ETL Limitations
1. Insert only. No updates. Null values inside `bronze_pdr_prediction` tables.
1. No backfilling data before `st_ts`. If you want to backfill drop all records or select a new `lake_path`.

## PredictoorJob - From subgraph to chart data
To provide summaries on Predidctoor users and systems, we want to fetch all new data and make it available for analysis.

PredictoorJob helps us achieve this by breaking the process down into 3 steps.
1. Ingesting + Loading Data - GQLDataFactory
1. Processing the data - ETL
1. Querying the data - Dash (TBD)

When these steps complete (1)(2), the final records are then used in dashbords (3) and other systems.
![Screenshot from 2024-02-29 13-51-46](https://github.com/oceanprotocol/pdr-backend/assets/69865342/8dc020e2-cf53-49d8-8327-9afc222e1750)

### PredictoorJob Workflow
To understand how this works a bit better, let's break this down into more detail.

#### Step 1 - GQLDataFactory - Fetching predictoor data [st_ts => end_ts] from subgraph into csv & lake.
1. Fetching the new raw data [st_ts => end_ts].
1. Saving it to CSV.
1. Saving it to the Lake.

#### Step 2 - ETL - (PredictoorJob) - Processing new raw data from sources through SQL queries.
1. Processing latest data + inserting w/ basic `INSERT SQL` query into `temp_table_data` inside lake.
1. Completing swap strategy to get `temp_table_data` into `prod_table_data`.

#### Step 3 - Dash - TBD

_There were already streamlit plots created for silver tables. Please read further._

## PredictoorJob Checkpointing
In order to only process new data, we want to "maintain a checkpoint" that helps us know where to start/resume from.

The simplest way to do this right now is to use the most frequent event we have in our data: **predictions submitted by predictoors**. We use this timestamp/checkpoint such that we only process new events, once.

By separating the RAW from the ETL data, at any point we should be able to (1) drop the ETL rows and rebuild them from raw. Making our data very flexible and forgiving to work with. 

_(1a) The cost do analyze all of predictoor may in the futurenot be cheap, but you should be able to downscale the date_range._

### Lake Stack st_ts => end_ts
All systems should be working in-sync... with the same [st_ts => end_ts] across all systems. In conjunction with ppss.yaml and everything else.
1. GQLDF fetches [st_ts => end_ts]
1. CSV saves [st_ts => end_ts]
1. PDS saves [st_ts => end_ts]
1. ETL processes + saves [st_ts => end_ts]
1. CLI/FE/Querying [st_ts => end_ts]

### Exception to the rule
This doesn't always have to be the case.
1. RAW + ETL Tables could have been dropped.
2. CSV + GQLDF => could be far ahead.
3. CLI/FE/Querying => would be limited to RAW + ETL tables & data

How to resolve a drop?
1. RAW + ETL Tables should be 1:1 => st_st.
2. CSV would be ahead. So we can take the max(timestamp) to know how far it is and where to sync-to => st_end
3. RAW Tables are rebuilt from CSV records.
4. ETL Tables are rebuilt from RAW tables.

All systems [GQLDF + CSV + RAW + ETL Updating] should be working as expected along w/ the cli & ppss.yaml.

## [PredictoorJob][Ingest + Load Step] - GQLDF Fetch + DuckDB Insert

GQL CSV and Lake max(timestamp) should remain 1:1 right now.
As new records are fetched, both of these should update atomically.

This process ends once all subgraph events have been written to duckdb tables.

### First Run - GQLDF Fetch + DuckDB Insert - No Records In Lake
When we start filling the lake, there will be no records to tell us where to resume from... So, we'll use ppss.yaml to get the lake_ss (1) st_ts and (2) end_ts.

GQLDataFactory will begin fetching from subgraph to fill the lake.
- from: ppss.lake_ss.st_ts - ie. 01-04-2024
- to: ppss.lake_ss.end_ts - ie. time.time()
- This is first appended into a CSV file
- Then this is inserted into lake (DuckDB via PDS)

**ETL Step does not begin until this completes successfully**

### Second+ Run - GQLDF Fetch + DuckDB Insert - Records Exist In Lake
When we resume updating the lake we can still initialize the run w/ ppss.yaml to get (1) st_ts ("01-04-2024") and (2) end_ts (now).... but we run some checks....
1. We can query the CSV to get `max(timestamp) from pdr_predictions` - 01-05-2024 - Which we can use as the `st_ts`.
1. We query the lake table to get `max(timestamp) from pdr_predictions` - 01-05-2024 - Which we can use as the `st_ts`

Providing us with the parmeters:
- from: 01-05-2024
- to: ppss.lake_ss.end_ts - i.e. time.time()
- This resumes fetching from where our data left off
- This provides us with a much smaller amount of events to fetch/join/update

**ETL Step does not begin until this completes successfully**

## [PredictoorJob][ETL + Process Step] - SQL Queries - Bronze/Silver/Gold Tables - No Updates

When inserting from raw data into duckdb, we try to clean up and enrich this data if possible, completing the first step. Now that the latest raw records have been written to DuckDB the ETL can kick off.

We want to start w/ updating the bronze_predictions table and other bronze_records since these reflect newly-arrived events.

However, many events and data points are not yet available when a prediction is submitted (like the payout). These values (and columns) remain null for now. 

The `bronze_pdr_prediction` query captures all parameters required to complete a pdr_prediction schema object, by joining across all table and related events (truevals, payouts) that are available in cold (old) data.

We now have to handle events as-they-are-happening in hot (new) data. (Incremental Updates)

# [TBD - TO COME] 

### [PredictoorJob][IncrementalJob][ETL]

Many data points are not yet available when a prediction is submitted (like the payout). There are many adjustments and improvements to the data that help enrich it like hadling predictoor_payout events when they arrive and updating the lake.

How: You write a SQL query that handles new pdr_payout events that happened in the last update period. This means we are now: handling events as-they-are-happening live and updating our records. (Incremental Updates)

Then: You join these events with existing records, to update their null fields, aggregates, and summaries.

We probably want to start w/ updating the bronze_predictions table and records when truevals & payouts happen.

_We had this before in polars, but not in SQL._

### Dash Plots

There were already streamlit plots created for silver tables. However, the silver queries and tables are not quite there yet.

Until then, if needed, bronze_prediction tables could be queried/charted via PDS.
1. Queries would be completed against lake via PDS by using `SELECT * FROM prod_data` and plotted into charts
1. Dash could then be used to display and interact with plots further.