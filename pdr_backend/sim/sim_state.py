from enforce_typing import enforce_types


# pylint: disable=too-many-instance-attributes
@enforce_types
class SimState:
    def __init__(self):
        self.iter_number = 0

        self.num_trades = 0
        self.num_correct_pred_in_trade = 0
        self.num_correct_pred_all = 0
        self.cum_profit = 0.0
