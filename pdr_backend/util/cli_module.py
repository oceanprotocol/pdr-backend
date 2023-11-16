
# pylint: disable=too-many-lines,too-many-statements
import argparse
import os
import sys

from enforce_typing import enforce_types
from eth_account import Account
from web3.main import Web3

from df_py.challenge import judge
from df_py.challenge.calc_rewards import calc_challenge_rewards
from df_py.challenge.csvs import (
    challenge_rewards_csv_filename,
    get_sample_challenge_data,
    get_sample_challenge_rewards,
    load_challenge_data_csv,
    load_challenge_rewards_csv,
    save_challenge_data_csv,
    save_challenge_rewards_csv,
)
from df_py.predictoor.csvs import (
    predictoor_data_csv_filename,
    save_predictoor_contracts_csv,
    save_predictoor_data_csv,
    save_predictoor_summary_csv,
)
from df_py.predictoor.queries import query_predictoor_contracts, query_predictoors
from df_py.util import blockrange, dispense, get_rate, networkutil, oceantestutil
from df_py.util.base18 import from_wei, to_wei
from df_py.util.blocktime import get_fin_block, timestr_to_timestamp
from df_py.util.contract_base import ContractBase
from df_py.util.dftool_arguments import (
    CHAINID_EXAMPLES,
    DfStrategyArgumentParser,
    SimpleChainIdArgumentParser,
    StartFinArgumentParser,
    autocreate_path,
    block_or_valid_date,
    chain_type,
    challenge_date,
    do_help_long,
    existing_path,
    print_arguments,
    valid_date,
    valid_date_and_convert,
)
from df_py.util.multisig import send_multisig_tx
from df_py.util.networkutil import DEV_CHAINID, chain_id_to_multisig_addr
from df_py.util.oceantestutil import (
    random_consume_FREs,
    random_create_dataNFT_with_FREs,
    random_lock_and_allocate,
)
from df_py.util.oceanutil import (
    FeeDistributor,
    OCEAN_token,
    record_deployed_contracts,
    veAllocate,
)
from df_py.util.retry import retry_function
from df_py.util.vesting_schedule import (
    get_active_reward_amount_for_week_eth,
    get_active_reward_amount_for_week_eth_by_stream,
)
from df_py.volume import calc_rewards, csvs, queries
from df_py.volume.calc_rewards import calc_rewards_volume





@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    func()
