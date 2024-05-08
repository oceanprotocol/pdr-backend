<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Lake, GQL Data Factory, and ETL Design

This README describes how you can use and operate the lake to understand the world of predictoor.

First, we want to make sure we get all the data we'll need! Then, we'll process this data so it's easy to chart and analyze things.

To complete all of these we'll be interacting many components in our data lake, like the GQLDataFactory and the ETL.

We'll get all of these covered in this README.

## Lake - Our Data Warehouse.
For most users, the lake can simply be thought of as a database. It should contain many tables with complete records and reliable information. It should be easy to understand and to work with.

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

GQLDataFactory - Fetching predictoor data from subgraph.
1. Collecting all raw data first and save it to CSV.
1. When we have all the CSV data saved, we can lookup the checkpoint inside the DW.
1. then saving it to CSV & PDS.

ETL - Processing data from sources through SQL queries.
1. Processing basic `INSERT SQL` queries, then saving it to a `temp_table_data` inside PDS
1. Completing swap strategy to get `temp_table_data` into `prod_table_data`.

### PredictoorETL Checkpointing
First Pass - Insert Records
- When we start filling the lake we'll use ppss.yaml to get the lake_ss (1) st_ts and (2) end_ts.
- GQLDataFactory will begin querying from the subgraph to get the data we'll need to fill the lake.
- This will give us the right time_range to fetch new records:
    - from: st_ts
    - to: now_timestamp

Second Pass - Records Exist
- When we resume updating the lake we'll use ppss.yaml to get the lake_ss (1) st_ts and (2) end_ts.
- When we resume updating the lake we'll query duckdb pdr-predictions, and get max(timestamp)
- This will give us the follow time_range to fetch new records:
    - from: max_timestamp_predictions
    - to: now_timestamp


