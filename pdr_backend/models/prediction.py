class Prediction:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        pair,
        timeframe,
        prediction,
        stake,
        trueval,
        timestamp,
        source,
        payout,
        user,
        submit_timestamp,
        prediction_id,
    ) -> None:
        self.pair = pair
        self.timeframe = timeframe
        self.prediction = prediction
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp
        self.source = source
        self.payout = payout
        self.user = user
        self.submit_timestamp = submit_timestamp
        self.prediction_id = prediction_id
