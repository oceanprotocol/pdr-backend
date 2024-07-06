from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.binmodel.binmodel import Binmodel
from pdr_backend.binmodel.binmodel_factory import BinmodelFactory
from pdr_backend.binmodel.test.resources import get_binmodel_data
from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict


@enforce_types
def test_binmodel_factory__attributes():
    f: BinmodelFactory = _get_binmodel_factory()
    assert isinstance(f.aimodel_ss, AimodelSS)


@enforce_types
def test_binmodel_factory__do_build():
    f: BinmodelFactory = _get_binmodel_factory()
    f.aimodel_ss.set_train_every_n_epochs(13)

    # case: no previous model
    assert f.do_build(None, 0)

    # case: have previous model; then on proper iter?
    prev_model = Mock(spec=Binmodel)
    assert f.do_build(prev_model, test_i=13 * 4)
    assert not f.do_build(prev_model, test_i=13 * 4 + 1)


@enforce_types
def test_binmodel_factory__build():
    f: BinmodelFactory = _get_binmodel_factory()

    data = get_binmodel_data()
    model = f.build(data)
    assert isinstance(model, Binmodel)

    p = model.predict_next(data.X_test)
    assert p is not None  # don't test further; leave that to test_binmodel.py


@enforce_types
def _get_binmodel_factory() -> BinmodelFactory:
    aimodel_ss = AimodelSS(aimodel_ss_test_dict())
    return BinmodelFactory(aimodel_ss)
