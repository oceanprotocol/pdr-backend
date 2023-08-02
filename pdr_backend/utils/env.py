import os
import sys

def get_rpc_url_or_exit() -> str:
    url = os.environ.get("RPC_URL", None)
    if url == None:
        print("You must set RPC_URL environment variable")
        sys.exit(1)
    return url

def get_subgraph_or_exit() -> str:
    url = os.environ.get("SUBGRAPH_URL", None)
    if url == None:
        print("You must set SUBGRAPH_URL environment variable")
        sys.exit(1)
    return os.environ.get("SUBGRAPH_URL", None)

def get_private_key_or_exit() -> str:
    private_key = os.environ.get("PRIVATE_KEY", None)
    if not private_key:
        print("You must set PRIVATE_KEY environment variable")
        sys.exit(1)
    return private_key

def get_pair_filter() -> str:
    return os.environ.get("PAIR_FILTER", None)

def get_timeframe_filter() -> str:
    return os.environ.get("TIMEFRAME_FILTER", None)

def get_source_filter() -> str:
    return os.environ.get("SOURCE_FILTER", None)

def get_owner_addresses() -> str:
    return os.environ.get("OWNER_ADDRS", None)