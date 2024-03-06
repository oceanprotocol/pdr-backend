import sys
import glob
import os
import pandas as pd
import duckdb


def csv_to_hive_partitioned_parquet(csv_folder_path):
    # List all CSV files in the folder
    csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

    for csv_file in csv_files:
        # Extract the file prefix (before "__")
        base_name = os.path.basename(csv_file)
        file_prefix = base_name.split("__")[0]

        # dtypes = {
        #     "timestamp": pl.Datetime,
        #     "open": pl.Float64,
        #     "high": pl.Float64,
        #     "low": pl.Float64,
        #     "close": pl.Float64,
        #     "volume": pl.Float64  # or pl.Int64 if you're sure volumes are always whole numbers
        # }
        # Create dtypes for pandas
        dtypes = {
            "timestamp": str,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,  # or pl.Int64 if you're sure volumes are always whole numbers
        }

        print(f"Processing {csv_file}...")
        # Read CSV into a Polars DataFrame
        # df = pl.read_csv(csv_file, dtypes=dtypes, has_header=True, infer_schema_length=100000)
        # DO IT with pandas

        df = pd.read_csv(csv_file, dtype=dtypes)
        # Add a new column for the stock name
        # Extract the stock name from the file prefix

        # df = df.with_columns([
        #     # Add a new column for the stock name
        #     pl.lit(file_prefix).alias('stock_name'),
        # ])

        # Do it with pandas
        df["stock_name"] = file_prefix

        # Using DuckDB to perform SQL operations and save to parquet with partitioning
        con = duckdb.connect(
            os.path.join(csv_folder_path, "persist.db")
        )  # Using in-memory database

        # Register Polars DataFrame as a view in DuckDB
        con.register("df_view", df)

        # Ensure timestamp column is cast to TIMESTAMP for extraction
        # Adjust the query to use correct syntax for extracting date parts
        con.execute(
            """
            CREATE VIEW processed_data AS
            SELECT *, 
                DATE_PART('year', CAST(timestamp AS TIMESTAMP)) as year,
                DATE_PART('month', CAST(timestamp AS TIMESTAMP)) as month,
                DATE_PART('day', CAST(timestamp AS TIMESTAMP)) as day
            FROM df_view
        """
        )

        # Define the path for the Hive-partitioned Parquet files
        parquet_path = os.path.join(csv_folder_path, "parquet")

        if not os.path.exists(parquet_path):
            # Create the directory if it doesn't exist
            os.makedirs(parquet_path)

        # Save the data to Parquet with partitioning by date
        query = f"COPY (SELECT * FROM processed_data) TO '{parquet_path}'  (FORMAT PARQUET, PARTITION_BY (stock_name, year, month, day), OVERWRITE_OR_IGNORE 1)"
        con.execute(query)

        # DROP the view to free up memory
        con.execute("DROP VIEW processed_data")

        print(
            f"Processed and saved {csv_file} to {parquet_path} with Hive partitioning."
        )


def basic_query_parquet(csv_folder_path, parquet_folder_path):
    con = duckdb.connect(
        os.path.join(csv_folder_path, "persist.db")
    )  # Using in-memory database

    # GET 5 of July 2018 records of SAIL stock,
    sql_query = f"""
        SELECT *
        FROM read_parquet('{parquet_folder_path}/stock_name=SAIL/year=2018/month=7/day=*/*.parquet')
        LIMIT 5
    """

    result = con.execute(sql_query)

    print(result.fetch_df())


def query_from_parquet(csv_folder_path, parquet_folder_path):
    con = duckdb.connect(
        os.path.join(csv_folder_path, "persist.db")
    )  # Using in-memory database

    sql_query = f"""
        WITH MonthlyStockData AS (
            SELECT 
                stock_name,
                MIN(day) AS first_day,
                MAX(day) AS last_day
            FROM read_parquet('{parquet_folder_path}/stock_name=*/year=2021/month=1/day=*/*.parquet')
            GROUP BY stock_name
        ),
        OpeningPrices AS (
            SELECT 
                m.stock_name,
                FIRST_VALUE(p.open) OVER(PARTITION BY m.stock_name ORDER BY p.timestamp ASC) AS opening_price
            FROM MonthlyStockData m
            JOIN read_parquet('{parquet_folder_path}/stock_name=*/year=2021/month=1/day=*/*.parquet') p
            ON m.stock_name = p.stock_name AND m.first_day = p.day
        ),
        ClosingPrices AS (
            SELECT 
                m.stock_name,
                LAST_VALUE(p.close) OVER(PARTITION BY m.stock_name ORDER BY p.timestamp ASC RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS closing_price
            FROM MonthlyStockData m
            JOIN read_parquet('{parquet_folder_path}/stock_name=*/year=2021/month=1/day=*/*.parquet') p
            ON m.stock_name = p.stock_name AND m.last_day = p.day
        ),
        StockIncreases AS (
            SELECT DISTINCT 
                o.stock_name,
                ((c.closing_price - o.opening_price) / o.opening_price) * 100 AS percentage_increase
            FROM OpeningPrices o
            JOIN ClosingPrices c
            ON o.stock_name = c.stock_name
        )
        SELECT *
        FROM StockIncreases
        ORDER BY percentage_increase DESC
    """

    result = con.execute(sql_query)

    print("Top 10 stocks by percentage increase in January 2021:")
    print(result.fetch_df().head(10))


def query_highest_lowest(csv_folder_path, parquet_folder_path):
    con = duckdb.connect(
        os.path.join(csv_folder_path, "persist.db")
    )  # Using in-memory database

    sql_query = f"""
        WITH MonthlyPriceRange AS (
            SELECT 
                stock_name,
                MAX(high) AS highest_price,
                MIN(low) AS lowest_price
            FROM read_parquet('{parquet_folder_path}/stock_name=*/year=2021/month=1/day=*/*.parquet')
            GROUP BY stock_name
        ),
        PriceDifferences AS (
            SELECT 
                stock_name,
                highest_price - lowest_price AS price_difference
            FROM MonthlyPriceRange
        )
        SELECT *
        FROM PriceDifferences
        ORDER BY price_difference DESC
        LIMIT 10
    """

    result = con.execute(sql_query)

    print("Top 10 stocks by percentage increase in January 2021:")
    print(result.fetch_df())


# Example usage
csv_folder_path = (
    "/Users/mac/Documents/projeler/OceanProtocol/pdr-backend/pdr-backend/csvs/"
)
# csv_to_hive_partitioned_parquet(csv_folder_path)
parquet_folder_path = (
    "/Users/mac/Documents/projeler/OceanProtocol/pdr-backend/pdr-backend/csvs/parquet"
)
# csv_to_hive_partitioned_parquet(csv_folder_path, parquet_folder_path)
# basic_query_parquet(csv_folder_path, parquet_folder_path)

# get function name from cli
function_name = sys.argv[1]
if function_name == "savedata":
    csv_to_hive_partitioned_parquet(csv_folder_path)
elif function_name == "query1":
    basic_query_parquet(csv_folder_path, parquet_folder_path)
elif function_name == "query2":
    query_from_parquet(csv_folder_path, parquet_folder_path)
elif function_name == "query3":
    query_highest_lowest(csv_folder_path, parquet_folder_path)
else:
    print("Invalid function name")
