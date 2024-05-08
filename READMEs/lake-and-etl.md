<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Lake, ETL, and our lord, data quality.

This README describes how you can operate the lake and use analytics to understand the world of predictoor.

First, we want to make sure we get all the data we'll need! Then, we'll process this data so it's easy to chart and undeerstand things.

To complete this we'll be interacting different components in our stack, such as the: lake, GQLDataFactory, and the ETL.

## Lake - Our Data Warehouse.
For most users, the lake can simply be thought of as a database. It should contain many tables with complete records and reliable information. It should be easy to understand and to work with. 

Currently, the Lake data can be accessed via the PersistentDataStore (PDS - DuckDB Wrapper) and operated with via via the cli (cli_module_lake.py).

Some features include:
1. The lake has a few commands: describe, validate, update, drop, and query
1. The lake is organized as a timeseries between st_ts and end_ts.
1. All the data inside lake tables exist between st_ts and end_ts.
1. The st_ts and end_ts checkpoints move as time progresses, new records are fetched, and processed.
1. The lake is designed so the raw data is only fetched once, then built many times.
1. The main work building the data will take place inside the ETL.
1. The lake does not support backfilling, you have to drop all data and then set a new ppss.lake_ss.st_ts.

## ETL - The jobs and queries that are run to build and keep the lake in great shape.

### Tyical ETL Workflow
1. Filling the lake with clean raw_predictions. Loading from Raw/CSV into DuckDB.
1. Cleaning it + Enriching it into bronze tables.
1. Aggregating + Summarizing it into silver & gold tables.
1. Being re-built and updated many times, in efficient ways.

### ETL Limitations
1. Insert only. No updates. Null values inside `bronze_pdr_prediction` tables.
1. No backfilling data before `st_ts`. If you want to backfill, please select a new `lake_path`.

## PredictoorETL - From subgraph to pretty charts
To provide summaries on Predidctoor users and systems, we want to fetch all of this data and make it available for analysis.

PredictoorETL helps us achieve this by breaking the process down into 2 steps.
1. Ingesting + Loading Data - GQLDataFactory
1. Processing the data - ETL

When these steps complete, the final records are then used in dashbords and other systems.
![Screenshot from 2024-02-29 13-51-46](https://github.com/oceanprotocol/pdr-backend/assets/69865342/8dc020e2-cf53-49d8-8327-9afc222e1750)

### PredictoorETL Workflow
To understand how this works a bit better, let's break this down into more detail.

GQLDataFactory - Fetching predictoor data from subgraph into csv & lake.
1. Fetching all raw data.
1. Saving it to CSV.
1. Saving it to lake

ETL - Processing data from sources through SQL queries.
1. Processing basic `INSERT SQL` queries and saving it to a `temp_table_data` inside lake
1. Completing swap strategy to get `temp_table_data` into `prod_table_data`.

### PredictoorETL Checkpointing
In order to only process new data, we want to "maintain a checkpoint" that let's us know where to start or resume from.

The simplest way to do this right now, is to use the most frequent event we'll have in our data: predictions submitted by predictoors. We use this timestamp checkpoint such that we process everything only once.

By separating the ETL from RAW data, at any point, we should be able to drop rows and re-processt them. Making our data very flexible to work with. _The cost do to this at scale may not be cheap, but you should be able to downscale the workload_

## GQLDF Fetch + DuckDB Insert - NO ETL

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

## ETL SQL Queries - Insert Step - Bronze Predictions - No Updating

Now that all raw records have been written to DuckDB, the ETL can kick off.

We probably want to start w/ updating the bronze_predictions table and records.

When inserting from raw data into duckdb, we try to clean up and enrich this data if possible. This lets us complete the most basic first step.

However, many data points are not yet available when a prediction is submitted (like the payout). These columns and values will be null for now. This query simply captures the old (cold) prediction data and all related events (truevals, payouts) that are already available.

We now have to handle events as-they-are-happening. (Incremental Updates)

### GQLDF + CSV + PDS + ETL Updating:

For this to work, 
1. GQLDF + CSV + PDS need to be working in-sync - same st_ts, end_ts - errors/events being handled well.
1. CSV vs. PDS may have different max(timestamp) => st_ts if not careful.

# [TO COME] 

### ETL - Incremental Update

Many data points are not yet available when a prediction is submitted (like the payout). There are many adjustments and improvements to the data that help enrich it like hadling predictoor_payout events when they arrive and updating the lake.

How: You write a SQL query that handles new pdr_payout events that happened in the last update period. This means we are now: handling events as-they-are-happening live and updating our records. (Incremental Updates)

Then: You join these events with existing records, to update their null fields, aggregates, and summaries.

We probably want to start w/ updating the bronze_predictions table and records when truevals & payouts happen.

_We had this before in polars, but not in SQL._

