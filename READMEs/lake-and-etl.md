<!--
Copyright 2024 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Lake & ETL Overview

This README describes how you can operate the lake and use analytics to understand the world of predictoor.

First, we want to make sure we get all the data we'll need! Then, we'll process this data so it's easy to chart and understand things.

To complete this we'll be interacting different components in our stack, such as the: Lake, GQLDataFactory, and the ETL.


## Content
- [**ETL Tables & Architecture**](#etl-tables--architecture)
- [**Lake - "Storage"**](#lake---storage)
- [**GQL Data Factory & RAW**](#gql-data-factory--raw-data)
- [**Data Warehouse - "Database"**](#data-warehouse---database)
- [**ETL**](#etl)
- [**Checkpoints**](#checkpoints)
- [**Dumb Components**](#dumb-components)
- [**Examples**](#examples)
- [**Dos and Don'ts**](#dos-and-donts)


## ETL Tables & Architecture
To provide summaries on Predidctoor users and systems, we want to fetch all new data and make it available for analysis.

The GraphQL Data Factory & ETL helps us achieve this by breaking the process down into 3 steps.
1. Ingesting + Loading Data - GQLDataFactory
1. Processing the data - ETL
1. Describing, visualization, and querying the data

The following diagram presents the ETL tables and workflow. Please maintain the [diagram](diagrams/lake.html) and image so they are up-to-date.
![Lake & ETL Tables](images/lake_tables_diagram.png)


## Lake - "Storage"
For most users, the lake can simply be thought of disk storage.

It contains many folders and CSVs, that maintain a complete set of records and reliable information. It should be easy to understand and to work with.

Currently, the lake (CSVs) can be accessed via the CSVDataStore (CSV wrapper) and operated with via the CLI module `lake raw` commands `pdr lake raw update ppss.yaml sapphire-mainnet` (cli_module_lake.py)

Some features include:
1. The lake has a few commands: `describe`, `validate`, `update`, `drop`, and `query`
1. The lake is made up of many timeseries objects that should exist from `lake_ss.st_ts` and `lake_ss.end_ts`.
1. All the data inside lake folders should exist between `st_ts` and `end_ts`.
1. The `st_ts` and `end_ts` checkpoints come from `ppss.yaml` and the `lake_ss` component.
1. You can set `st_ts` and `end_ts` to relative times ("3 hours ago" -> "now"), so new new records are always fetched and processed.
1. The lake is designed so raw data is fetched only once from subgraph and then saved into `lake_data/` and DuckDB.

**Note:** The lake currently does not support backfilling. If you need to, drop all data, adjust `st_ts` and `end_ts`, and then fetch again.


## GQL Data Factory & Raw Data
Is responsible for running a series of graphql fetches against subgraphs and then saves this raw data into the lake (CSV).  

Because GQL Data Factory is responsible for "Ingesting & Loading", we piggy back on this routine and also plce this raw data into our data warehouse (DuckDB).

When the GQL Data Factory updates, it looks at each query and their respective `lake_data/` folder to figure out where to resume from. Once all data has been fetched and loaded into `lake_data/` and the Data Warehouse (DuckDB), the update routine ends.

**Note:** The lake is designed to only be filled once. By default GQL Data Factory will not delete data from `lake_data/`. This is done intentionally.

If you want to refetch parts of your lake data:
1. Delete the `lake_data` folder
```console
sudo rm -r lake_data/
```

2. Drop all records from the Data Warehouse
```
```console
pdr lake raw drop ppss.yaml sapphire-mainnet 2020-01-01
pdr lake etl drop ppss.yaml sapphire-mainnet 2020-01-01
```

3. Fetch the data again (if required, update `st_ts` and `end_ts`)
```console
pdr lake raw update ppss.yaml sapphire-mainnet
```

## Data Warehouse - "Database"
For most users, the Data Warehouse (DuckDB) is just a database.

To deliver a complete data stack capable of storing, processing, and enriching all of our data, we load all CSVs (lake) into DuckDB (DW) and then process this data through a series of SQL queries (ETL) inside the DW.

Currently, the DW (DB) can be accessed via the DuckDBDataStore (DuckDB Wrapper) and operated with via the CLI module `lake` commands `pdr lake etl update ppss.yaml sapphire-mainnet` (cli_module_lake.py)

Some features include:
1. The DW is atomic and designed to be destroyed/rebuilt by leveraging raw data from `lake_data`. There are no migrations.
1. To rebuild the DW, please use a combination of `lake etl drop` and `lake etl update` commands.
1. The DW is rebuilt using a series of SQL queries that Extract-Transform-Load (ETL) into new tables.
1. All ETL SQL queries run on DuckDB and follow a "mini-batch" routine to be as efficient as possible.
1. ETL tables use a "Medallion Achitecture" (bronze, silver, gold) to deliver a structured ETL architecture.
1. All the data inside ETL tables exist between `st_ts` and `end_ts`.

**Note:** All ETL is done on the DW to be efficient and future-proof ourselves towards distributed DBs. Do not jump between python -> sql -> python, this is computationally and memory expensive. All queries are designed to function as mini-batch opeations to reduce the amount of scans, joins, inserts, and updates.


## ETL
Is responsible for running a series of Jobs and queries that keep the lake in great shape.

### Update from CLI
From the cli - `pdr lake etl update ppss.yaml sapphire-mainnet`

### Data Flow
As you are developing and building around the data and lake, you might need to update how the system works, and be able to follow this workflow.
1. GQLDF completes succesfully. Fetch from source RAW => into CSV & DuckDB.
1. ETL runs SQL queries over the RAW data to clean it, join w/ other tables, transform => into Bronze Tables
1. Aggregating + Summarizing it => into Silver & Gold tables.
1. Serving this data into dahboards and other locations.

### Workflow
As you are developing and building around the lake, your workflow migh look like this.
1. Writing & Updating ETL code
1. Dropping ETL tables via CLI
1. Rebuilding ETL tables via CLI

### Limitations
1. No backfilling data before `st_ts`. If you want to backfill drop all records or select a new `lake_path`.


## Checkpoints

In order to only process new data, we want to "maintain a checkpoint" that helps us know where to start/resume from.

The simplest way to do this is to use the first and last event timestamps from our data.

### GQL Data Factory
All CSVs should be in-sync... with nearly the same [st_ts => end_ts] across all folders.
1. GQLDF fetches [st_ts => end_ts] from CSVs if available so it can resume, otherwise it uses ppss.yaml `st_ts`
1. For each GQL, we fetch all records [st_ts => end_ts] and save them as they arrive
1. Write raw data to CSV [st_ts => end_ts]
1. Write raw data to DW [st_ts => end_ts]

### ETL
All ETL tables should be in-sync with nearly the same [st_ts => end_ts].
1. ETL looks at CSV and ETL Tables last_records to identify how to resume [st_ts => end_ts], otherwise it uses ppss.yaml.
1. ETL begins by process all RAW records [st_ts => end_ts] before processing the ETL tables.
1. RAW records are processed into NewEvents (INSERT) and UpdateEvents(UPDATE) and stored in temporary tables.
1. All NewEvents and UpdateEvents [st_ts => end_ts] from RAW tables, are used to update bronze tables.

**Exceptions to the rule**
This doesn't always have to be the case.
1. RAW + ETL records could have been dropped.
2. CSV + GQLDF could be far ahead.

**How to resolve a drop?**
1. Run `describe` and `validate` to make sure there are no errors.
2. Drop all RAW + ETL Tables from DW and rebuild the DW from scratch.
3. RAW Tables are rebuilt from CSV records.
4. ETL Tables are rebuilt from RAW tables.

All systems [GQLDF + ETL + CSV + DuckDB] should be working out-of-the-box by using ppss.yaml & the cli.


## "Dumb" Components
Components should be self-contained, "dumb", and perform one role.

GQLDF is upstream from ETL and does not have any knowledge of it. Do not create dependencies where there are none.

If you delete data from `lake_data`, do not expect this change to be reflected in RAW or ETL tables.

Rather, think about the DX, entry points, and [how to approach this intuitively](https://github.com/oceanprotocol/pdr-backend/issues/1087#issuecomment-2155527087) so these checks are built into the DX and easy-to-use.


## Examples & How To's

### Run Lake end to end

1. Fetch the data and create the Lake with **RAW** and **ETL** data
```console
pdr lake etl update ./ppss.yaml sapphire-mainnet
```
2. Validate the Lake
```console
pdr lake validate ./ppss.yaml sapphire-mainnet 
```
3. Inspect the Lake
```console
pdr lake describe ./ppss.yaml sapphire-mainnet 
```
4. Query data from the Lake
```console
pdr lake query ./lake_data "SELECT * FROM pdr_predictions"
```


### Modify Lake data
5. Drop data from the Lake at **ETL** level starting from a specified date
```console
pdr lake etl drop ppss.yaml sapphire-mainnet 2024-01-10
```

6. Drop data from the Lake at **RAW** level starting from a specified date
```console
pdr lake raw drop ppss.yaml sapphire-mainnet 2024-01-10
```

7. Recover data at **RAW** level starting from a specified date
```console
pdr lake raw update ppss.yaml sapphire-mainnet
```

8. Recover data at **ETL** level starting from a specified date
```console
pdr lake etl update ppss.yaml sapphire-mainnet
```

9. Validate the Lake
```console
pdr lake validate ppss.yaml sapphire-mainnet 
```

## DO'S and DONT'S
**Don't**:
 - !! Don't modify the CSV files in any way, otherwise data is going to be eronated !!

**Do's**:
 - If data is eronated or there is any issue with the Lake, reset the lake
 - Reset the Lake by deleting `lake_data/` folder
 - Recreate the Lake by running `lake raw update` and `lake etl update` commands
