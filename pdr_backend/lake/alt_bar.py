from typing import Union
import numpy as np

from enforce_typing import enforce_types
import pandas as pd

# add config pair: volume_threshold in ppss


@enforce_types
def _extract_bars(
    data: pd.DataFrame, metric: str, threshold: Union[float, int] = 50000
):
    """
    For loop which compiles the various bars: dollar, volume, or tick.

    :param data: raw ohlcv data from kaiko Contains 6 columns
                - timestamp, open, high, low, close and volume.
    :param metric: cum_ticks, cum_dollar_value, cum_volume
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :return: list of bars and updated start timestamp since last bar.
    """

    list_bars = []
    start_tm = None
    cum_ticks = 0
    cum_dollar_value = 0.0
    cum_volume = 0.0
    bar_cache = []
    high_price = -np.inf
    low_price = np.inf

    # Iterate over rows
    for row in data.values:
        # Set variables
        timestamp = row[0]
        open_price = float(row[1])
        high = float(row[2])
        low = float(row[3])
        close = float(row[4])
        volume = float(row[5])

        # Calculations
        cum_ticks += 1
        dollar_value = close * volume
        cum_dollar_value = cum_dollar_value + dollar_value
        cum_volume = cum_volume + volume

        # Check min max
        high_price = max(high_price, high)
        low_price = min(low_price, low)

        # Update cache
        bar_cache.append(
            [
                timestamp,
                open_price,
                high_price,
                low_price,
                close,
                cum_volume,
                cum_dollar_value,
                cum_ticks,
            ]
        )

        # If threshold reached then take a sample
        if eval(metric) >= threshold:  # pylint: disable=eval-used
            # Create bars
            start_tm = timestamp
            tp = bar_cache[0][0]
            open_price = bar_cache[0][1]
            low_price = min(low_price, low)
            high_price = max(high_price, high)
            close_price = close

            # Update bars & Reset counters
            list_bars.append(
                [
                    tp,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    cum_volume,
                    cum_dollar_value,
                    cum_ticks,
                ]
            )
            cum_ticks = 0
            cum_dollar_value = 0.0
            cum_volume = 0.0
            bar_cache = []
            high_price = -np.inf
            low_price = np.inf

    if not start_tm:
        start_tm = bar_cache[0][0]
    return list_bars, start_tm


def get_dollar_bars(rawohlcv_df: pd.DataFrame, threshold: float):
    """
    Creates the dollar bars: timestamp, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    :param rawohlcv: from kaiko
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :return: list of of dollar bars and updated starting timestamp
    """
    list_bars, newest_ut_value = _extract_bars(
        rawohlcv_df, metric="cum_dollar_value", threshold=threshold
    )
    return list_bars, newest_ut_value


def get_volume_bars(rawohlcv_df: pd.DataFrame, threshold: float):
    """
    Creates the volume bars: date_time, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    :param rawohlcv: from kaiko
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :return: list of of dollar bars and updated starting timestamp
    """
    list_bars, newest_ut_value = _extract_bars(
        rawohlcv_df, metric="cum_volume", threshold=threshold
    )
    return list_bars, newest_ut_value


def get_tick_bars(rawohlcv_df: pd.DataFrame, threshold: float):
    """
    Creates the tick bars: date_time, open, high, low, close, cum_vol, cum_dollar, and cum_ticks.

    :param rawohlcv: from kaiko
    :param threshold: A cumulative value above this threshold triggers a sample to be taken.
    :return: list of of dollar bars and updated starting timestamp
    """
    list_bars, newest_ut_value = _extract_bars(
        rawohlcv_df, metric="cum_ticks", threshold=float(int(threshold))
    )
    return list_bars, newest_ut_value
