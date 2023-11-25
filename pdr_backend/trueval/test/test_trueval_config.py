import os
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.env import parse_filters


def test_trueval_config():
    config = TruevalConfig()
    assert config.rpc_url == os.getenv("RPC_URL")
    assert config.subgraph_url == os.getenv("SUBGRAPH_URL")
    assert config.private_key == os.getenv("PRIVATE_KEY")
    assert config.sleep_time == int(os.getenv("SLEEP_TIME", "30"))
    assert config.batch_size == int(os.getenv("BATCH_SIZE", "30"))

    (f0, f1, f2, f3) = parse_filters()
    assert config.pair_filters == f0
    assert config.timeframe_filter == f1
    assert config.source_filter == f2
    assert config.owner_addresses == f3
