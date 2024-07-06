from typing import Optional

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.binmodel.binmodel import Binmodel
from pdr_backend.binmodel.binmodel_data import BinmodelData
from pdr_backend.binmodel.constants import UP, DOWN
from pdr_backend.ppss.aimodel_ss import AimodelSS


class BinmodelFactory:
    @enforce_types
    def __init__(self, aimodel_ss: AimodelSS):
        self.aimodel_ss = aimodel_ss

    @enforce_types
    def do_build(self, prev_model: Optional[Binmodel], test_i: int) -> bool:
        """Update/train model?"""
        n = self.aimodel_ss.train_every_n_epochs
        return prev_model is None or test_i % n == 0

    @enforce_types
    def build(self, data: BinmodelData) -> Binmodel:
        model_f = AimodelFactory(self.aimodel_ss)

        model_UP = model_f.build(
            data[UP].X_train,
            data[UP].ytrue_train,
            None,
            None,
        )

        model_DOWN = model_f.build(
            data[DOWN].X_train,
            data[DOWN].ytrue_train,
            None,
            None,
        )

        binmodel = Binmodel(model_UP, model_DOWN)
        return binmodel
