from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.grpmodel.grpmodel import Grpmodel
from pdr_backend.grpmodel.grpmodel_factory import GrpmodelFactory
from pdr_backend.grpmodel.test.resources import get_grpmodel_data


@enforce_types
def test_grpmodel_factory__attributes():
    f: GrpmodelFactory = _get_grpmodel_factory()
    assert isinstance(f.aimodel_ss, AimodelSS)


@enforce_types
def test_grpmodel_factory__do_build():
    f: GrpmodelFactory = _get_grpmodel_factory()
    f.aimodel_ss.set_train_every_n_epochs(13)

    # case: no previous model
    assert f.do_build(None, 0)

    # case: have previous model; then on proper iter?
    prev_model = Mock(spec=Grpmodel)
    assert f.do_build(prev_model, test_i=13 * 4)
    assert not f.do_build(prev_model, test_i=13 * 4 + 1)


@enforce_types
def test_grpmodel_factory__build():
    f: GrpmodelFactory = _get_grpmodel_factory()

    data = get_grpmodel_data()
    model = f.build(data)
    assert isinstance(model, Grpmodel)

    p = model.predict_next(data.X_test)
    assert p is not None  # don't test further; leave that to test_grpmodel.py


@enforce_types
def _get_grpmodel_factory() -> GrpmodelFactory:
    aimodel_ss = AimodelSS(aimodel_ss_test_dict())
    return GrpmodelFactory(aimodel_ss)
