from typing import List, Union

from enforce_typing import enforce_types


@enforce_types
class Prediction:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        contract: str,
        pair: str,
        timeframe: str,
        prediction: Union[bool, None],  # prediction = subgraph.predicted_value
        stake: Union[float, None],
        trueval: Union[bool, None],
        timestamp: int,  # timestamp == prediction submitted timestamp
        source: str,
        payout: Union[float, None],
        slot: int,  # slot/epoch timestamp
        address: str,
        user: str,
    ) -> None:
        self.ID = ID
        # self.prediction_id = f"{contract}-{slot}-{user}"
        # self.payout_id = f"{contract}-{slot}-{user}"
        # self.slot_id = f"{contract}-{slot}"
        # self.trueval_id = f"{contract}-{slot}"
        self.contract = contract
        self.pair = pair
        self.timeframe = timeframe
        self.prediction = prediction
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp
        self.source = source
        self.payout = payout
        self.slot = slot
        self.address = (address,)
        self.user = user


# =========================================================================
# utilities for testing


@enforce_types
def mock_prediction(prediction_tuple: tuple) -> Prediction:
    (
        contract,
        pair_str,
        timeframe_str,
        prediction,
        stake,
        trueval,
        timestamp,
        source,
        payout,
        slot,
        address,
        user,
    ) = prediction_tuple

    ID = f"{contract}-{slot}-{user}"
    return Prediction(
        ID=ID,
        contract=contract,
        pair=pair_str,
        timeframe=timeframe_str,
        prediction=prediction,
        stake=stake,
        trueval=trueval,
        timestamp=timestamp,
        source=source,
        payout=payout,
        address=address,
        slot=slot,
        user=user,
    )


@enforce_types
def mock_first_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple) for prediction_tuple in _FIRST_PREDICTION_TUPS
    ]


@enforce_types
def mock_second_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in _SECOND_PREDICTION_TUPS
    ]


@enforce_types
def mock_daily_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple) for prediction_tuple in _DAILY_PREDICTION_TUPS
    ]


_FIRST_PREDICTION_TUPS = [
    (
        "0xaaaa",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        False,
        1701503000,
        "binance",
        0.0,
        1701503100,
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xbbbb",
        "BTC/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701589400,
        "binance",
        0.0,
        1701589500,
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152",
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]

_SECOND_PREDICTION_TUPS = [
    (
        "0xeeee",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701675800,
        "binance",
        0.0500,
        1701675900,
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xbbbb",
        "BTC/USDT",
        "1h",
        True,
        0.0500,
        False,
        1701503100,
        "binance",
        0.0,
        1701503000,
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xaaaa",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701589400,
        "binance",
        0.0500,
        1701589500,
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xbnnn",
        "BNB/USDT",
        "1h",
        True,
        0.0500,
        True,
        1701675800,
        "kraken",
        0.0500,
        1701675900,
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd",
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xeeee",
        "ETH/USDT",
        "1h",
        True,
        None,
        False,
        1701589400,
        "binance",
        0.0,
        1701589500,
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "0xcccc4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xeeee",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701675800,
        "binance",
        0.0500,
        1701675900,
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]

_DAILY_PREDICTION_TUPS = [
    (
        "0xeeee",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1698865200,  # Nov 01 2023 19:00:00 GMT
        "binance",
        0.0500,
        1698865200,
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xbbbb",
        "BTC/USDT",
        "1h",
        True,
        0.0500,
        False,
        1698951600,  # Nov 02 2023 19:00:00 GMT
        "binance",
        0.0,
        1698951600,
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xaaaa",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        True,
        1699038000,  # Nov 03 2023 19:00:00 GMT
        "binance",
        0.0500,
        1699038000,
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xbnnn",
        "BNB/USDT",
        "1h",
        True,
        0.0500,
        True,
        1699124400,  # Nov 04 2023 19:00:00 GMT
        "kraken",
        0.0500,
        1699124400,
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xeeee",
        "ETH/USDT",
        "1h",
        True,
        None,
        False,
        1699214400,  # Nov 05 2023 19:00:00 GMT
        "binance",
        0.0,
        1701589500,
        "0xaa6515c138183303b89b98aea756b54f711710c5",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xeeee",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1699300800,  # Nov 06 2023 19:00:00 GMT
        "binance",
        0.0500,
        1699300800,
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]