from enforce_typing import enforce_types

from pdr_backend.ppss.payout_ss import PayoutSS


@enforce_types
def test_payout_ss():
    d = {"batch_size": 50}
    ss = PayoutSS(d)
    assert ss.batch_size == 50

    ss.set_batch_size(5)
    assert ss.batch_size == 5
