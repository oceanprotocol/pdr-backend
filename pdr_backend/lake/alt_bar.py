import logging
from typing import List, Union
import numpy as np

from enforce_typing import enforce_types
import pandas as pd

logging = logging.getLogger("volume_bar")

# add config pair: volume_threshold in ppss

def _extract_bars(data, metric, threshold=50000):
    """
    For loop which compiles the various bars: dollar, volume, or tick.

    We did investigate the use of trying to solve this in a vectorised manner but found that a For loop worked well.

    :param data: raw ohlcv data from kaiko Contains 6 columns - timestamp, open, high, low, close and volume.
    :param metric: cum_ticks, cum_dollar_value, cum_volume
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :return: The financial data structure with the cache of short term history.
    """

    list_bars = []
    cum_ticks, cum_dollar_value, cum_volume, high_price, low_price = 0, 0, 0, -np.inf, np.inf


    # Iterate over rows
    for row in data.values:
        # Set variables
        timestamp = row[0]
        price = float(row[4])  # use close price
        open_price = float(row[1])
        high = float(row[2])
        low = float(row[3])
        volume = row[5]

        # Calculations
        cum_ticks += 1
        dollar_value = price * volume
        cum_dollar_value = cum_dollar_value + dollar_value
        cum_volume = cum_volume + volume

        # Check min max
        if high > high_price:
            high_price = high
        if low <= low_price:
            low_price = low

        # Update cache
        cache.append([timestamp, open_price, low_price, high_price, cum_volume, cum_dollar_value, cum_ticks])

        # If threshold reached then take a sample
        if eval(metric) >= threshold:   # pylint: disable=eval-used
            # Create bars
            open_price = cache[0][1]
            low_price = min(low_price, low)
            close_price = price

            # Update bars & Reset counters
            list_bars.append([timestamp, open_price, high_price, low_price, close_price,
                              cum_volume, cum_dollar_value, cum_ticks])
            cum_ticks, cum_dollar_value, cum_volume, cache, high_price, low_price = 0, 0, 0, [], -np.inf, np.inf

    return list_bars, cache


def get_dollar_bars(rawohlcv_df, threshold=70000000):
    """
    Creates the dollar bars: timestamp, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    Following the paper "The Volume Clock: Insights into the high frequency paradigm" by Lopez de Prado, et al,
    it is suggested that using 1/50 of the average daily dollar value, would result in more desirable statistical
    properties.

    :param file_path: File path pointing to csv data.
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :return: Dataframe of dollar bars
    """
    list_bars, cache = _extract_bars(rawohlcv_df, metric='cum_dollar_value', threshold=threshold)
    newest_ut_value = cache[0]["timestamp"]
    return list_bars, newest_ut_value

def get_volume_bars(rawohlcv_df, threshold):
    """
    Creates the volume bars: date_time, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    Following the paper "The Volume Clock: Insights into the high frequency paradigm" by Lopez de Prado, et al,
    it is suggested that using 1/50 of the average daily volume, would result in more desirable statistical properties.

    :param file_path: File path pointing to csv data.
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :return: Dataframe of volume bars
    """
    list_bars, cache = _extract_bars(rawohlcv_df, metric='cum_volume', threshold=threshold)
    newest_ut_value = cache[0]["timestamp"]
    return list_bars, newest_ut_value

def get_tick_bars(rawohlcv_df, threshold):
    """
    Creates the tick bars: date_time, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    :param file_path: File path pointing to csv data.
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :return: Dataframe of tick bars
    """
    list_bars, cache = _extract_bars(rawohlcv_df, metric='cum_tick', threshold=threshold)
    newest_ut_value = cache[0]["timestamp"]
    return list_bars, newest_ut_value