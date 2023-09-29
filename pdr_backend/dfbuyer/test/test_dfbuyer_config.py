import os
from pdr_backend.dfbuyer.dfbuyer_config import DFBuyerConfig
from pdr_backend.util.env import parse_filters


def test_trueval_config():
    config = DFBuyerConfig()
    assert config.rpc_url == os.getenv("RPC_URL")
    assert config.subgraph_url == os.getenv("SUBGRAPH_URL")
    assert config.private_key == os.getenv("PRIVATE_KEY")
    assert config.batch_size == int(os.getenv("CONSUME_BATCH_SIZE", "20"))
    assert config.weekly_spending_limit == int(
        os.getenv("WEEKLY_SPENDING_LIMIT", "37000")
    )
    assert config.consume_interval_seconds == int(
        os.getenv("CONSUME_INTERVAL_SECONDS", "86400")
    )

    (f0, f1, f2, f3) = parse_filters()
    assert config.pair_filters == f0
    assert config.timeframe_filter == f1
    assert config.source_filter == f2
    assert config.owner_addresses == f3
