import ccxt
import csv
from datetime import datetime
import polars as pl
from pdr_backend.lake.constants import (
    TOHLCV_SCHEMA_PL,
)
# Helper function to convert OHLCV data to Unix timestamps
def _ohlcv_to_uts(tohlcv_data):
    return [row[0] for row in tohlcv_data]

# Function to filter data within a specified time range
def _filter_within_timerange(tohlcv_data, st_ut, fin_ut):
    uts = _ohlcv_to_uts(tohlcv_data)
    return [vec for ut, vec in zip(uts, tohlcv_data) if st_ut <= ut <= fin_ut]


# Initialize Binance exchange
exchange = ccxt.binanceus()

# Define the symbol and timeframe
symbol = 'BTC/USDT'
timeframe = '1m'  # 1 minute timeframe

# Fetch historical data
data = exchange.fetch_ohlcv(symbol, timeframe, since=1708548000000, limit=1000)

# Specify the CSV file name
csv_filename = './historical_data.csv'

# Save data to CSV
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file, delimiter=',')
    # Write the header
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # Write the data rows
    for row in data:
        writer.writerow(row)

# Example start and finish Unix timestamps for filtering
start_ut = 1708537200000  # Adjust to your specific start time
finish_ut = 1708597140000  # Adjust to your specific end time

# Filter the data
filtered_data = _filter_within_timerange(data, start_ut, finish_ut)

#check if the timestamp includes a float
for row in filtered_data:
    if type(row[0]) == float:
        print(row[0])

# Save the filtered data to a CSV file
csv_filename = './filtered_data.csv'
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    writer.writerows(filtered_data)

next_df = pl.DataFrame(filtered_data, schema=TOHLCV_SCHEMA_PL)


print(f"Filtered data successfully saved to {csv_filename}")