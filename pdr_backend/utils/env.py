import os
import sys

def get_envvar(envvar_name: str, default=None) -> str:
    return os.environ.get(envvar_name, default)

def get_envvar_or_exit(envvar_name: str) -> str:
    value = get_envvar(envvar_name)
    if value == None:
        print(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value

def get_rpc_url_or_exit() -> str:
    return get_envvar_or_exit("RPC_URL")

def get_subgraph_or_exit() -> str:
    return get_envvar_or_exit("SUBGRAPH_URL")

def get_private_key_or_exit() -> str:
    return get_envvar_or_exit("PRIVATE_KEY")

def get_pair_filter() -> str:
    return get_envvar("PAIR_FILTER")

def get_timeframe_filter() -> str:
    return get_envvar("TIMEFRAME_FILTER")

def get_source_filter() -> str:
    return get_envvar("SOURCE_FILTER")

def get_owner_addresses() -> str:
    return get_envvar("OWNER_ADDRS")