<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Lake, GQL Data Factory, and ETL Design

This README describes how you can use and operate the lake to understand the world of predictoor.

First, we want to make sure we get all the data we'll need! Then, we'll process this data so it's easy to chart and analyze things.

To complete all of these we'll be interacting many components in our data lake, like the GQLDataFactory and the ETL.

We'll get all of these covered in this README.

## Lake - A collection of timeseries data, aggregates, and summaries that give us a complete picture of our data. 

### 1. The lake has a few commands: describe, validate, update, drop, and query 
### 2a. The lake is organized as a timeseries between st_ts and end_ts
### 2b. This checkpoint moves as new predictions are fetched and recorded into pdr_predictions. 
### 3. The lake does not support rollbacks, you have to drop everything and start over
### 4. The lake is designed to only be fetched once

## ETL - A set of queries that create rich data and help us understand how things are performing   

### 1. Filling the lake with raw_predictions
### 2. Cleaning and enriching it into bronze_predictions
### 3. Unlike th lake being designed to only be fetched once, the ETL is designed to be built many times

First Pass - No Records
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
