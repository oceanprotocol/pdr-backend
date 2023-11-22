from pdr_backend.trueval.trueval_ss import TruevalSS


def test_trueval_ss():
    d = {"sleep_time": 30, "batch_size": 50}
    ss = TruevalSS(d)
    assert ss.sleep_time == 30
    assert ss.batch_size == 50
