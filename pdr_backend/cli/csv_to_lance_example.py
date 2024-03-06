import glob
import os
import sys
import polars as pl
import lancedb  # Import LanceDB
import pandas as pd
import pyarrow as pa
from memory_profiler import profile


def store_csv_in_lance(csv_folder_path):
    uri = os.path.join(csv_folder_path, "sample.lancedb")
    db = lancedb.connect(uri)

    csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

    # transform it to pyarrow schema
    schema = pa.schema(
        [
            pa.field("stock_name", pa.string()),
            pa.field("timestamp", pa.timestamp("ns", tz="UTC")),
            pa.field("open", pa.float64()),
            pa.field("high", pa.float64()),
            pa.field("low", pa.float64()),
            pa.field("close", pa.float64()),
            pa.field(
                "volume", pa.float64()
            ),  # Use pa.int64() if you are sure volumes are always whole numbers
        ]
    )

    # check path exists
    if not os.path.exists(uri):
        os.makedirs(uri)

    table_path = os.path.join(uri, "stock_data.lance")
    if os.path.exists(table_path):
        db.drop_table("stock_data")

    table = db.create_table("stock_data", schema=schema)

    for csv_file in csv_files:
        base_name = os.path.basename(csv_file)
        stock_name = base_name.split("__")[0]

        dtypes = {
            "timestamp": str,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,  # or pl.Int64 if you're sure volumes are always whole numbers
        }
        # Read CSV into a Polars DataFrame with the appropriate dtypes
        df = pd.read_csv(
            csv_file,
            dtype=dtypes,
            parse_dates=["timestamp"],
            date_format="%Y-%m-%d %H:%M:%S",
        )

        # Add stock_name column
        df["stock_name"] = stock_name

        # Store in LanceDB
        table.add(df)

        print(f"Data for {stock_name} stored in LanceDB.")


@profile
def execute_lance_query(csv_folder_path):
    # EN: Connect to the LanceDB
    uri = os.path.join(csv_folder_path, "sample.lancedb")
    db = lancedb.connect(uri)
    tbl = db.open_table("stock_data")
    tbl_lazy = tbl.to_polars()

    # EN: Filter by year and month
    filtered_df = tbl_lazy.filter(
        (pl.col("timestamp").dt.year() == 2021) & (pl.col("timestamp").dt.month() == 1)
    )

    # En: Group by stock_name and calculate max high and min low
    grouped_df = filtered_df.group_by("stock_name").agg(
        [pl.max("high").alias("max_high"), pl.min("low").alias("min_low")]
    )

    # 'max_high' ve 'min_low' diff
    differed_df = grouped_df.with_columns(
        (pl.col("max_high") - pl.col("min_low")).alias("diff-month")
    )

    # Diff sort and limit
    result_df = differed_df.sort("diff-month", descending=True).limit(10)

    # calculate
    sonuc = result_df.collect()
    print(sonuc)


if __name__ == "__main__":
    # Example usage
    csv_folder_path = (
        "/Users/mac/Documents/projeler/OceanProtocol/pdr-backend/pdr-backend/csvs/"
    )

    # get function name from cli
    function_name = sys.argv[1]
    if function_name == "savedata":
        store_csv_in_lance(csv_folder_path)
    elif function_name == "query1":
        execute_lance_query(csv_folder_path)
    else:
        print("Invalid function name")
