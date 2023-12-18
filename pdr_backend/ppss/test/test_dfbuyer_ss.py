from pdr_backend.ppss.dfbuyer_ss import DFBuyerSS


def test_trueval_config():
    ss = DFBuyerSS(
        {
            "batch_size": 42,
            "consume_interval_seconds": 42,
            "weekly_spending_limit": 42 * 7 * 24 * 3600,
        }
    )
    assert ss.batch_size == 42
    assert ss.weekly_spending_limit == 42 * 7 * 24 * 3600
    assert ss.consume_interval_seconds == 42
    assert ss.amount_per_interval == 42 * 42
