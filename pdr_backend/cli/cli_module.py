#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import sys

from enforce_typing import enforce_types

from pdr_backend.analytics.check_network import check_network_main
from pdr_backend.analytics.get_predictions_info import (
    get_predictions_info_main,
    get_predictoors_info_main,
    get_traction_info_main,
)
from pdr_backend.cli.cli_arguments import (
    do_help_long,
    do_help_short,
    get_arg_parser,
    print_args,
)
from pdr_backend.deployer.deployer import main as deployer_main
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.cli.cli_arguments_lake import LAKE_SUBCOMMANDS
from pdr_backend.cli.cli_module_lake import do_lake_subcommand
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.payout.payout import do_ocean_payout, do_rose_payout
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.pred_submitter.deploy import deploy_pred_submitter_mgr_contract
from pdr_backend.predictoor.predictoor_agent import PredictoorAgent
from pdr_backend.publisher.publish_assets import publish_assets
from pdr_backend.sim.multisim_engine import MultisimEngine
from pdr_backend.sim.sim_dash import sim_dash
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.statutil.arima_dash import arima_dash
from pdr_backend.analytics.predictoor_dashboard.predictoor_dash import predictoor_dash
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trueval.trueval_agent import TruevalAgent
from pdr_backend.util.core_accounts import fund_accounts_with_OCEAN
from pdr_backend.util.currency_types import Eth
from pdr_backend.util.topup import topup_main
from pdr_backend.util.web3_accounts import (
    create_accounts,
    fund_accounts,
    print_balances,
)

logger = logging.getLogger("cli")


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_short(0)
    if sys.argv[1] == "help_long":
        do_help_long(0)

    print("do_lake_submcommand: parsed_args:", sys.argv[1:])

    if sys.argv[1] == "lake" and sys.argv[2] in LAKE_SUBCOMMANDS:
        do_lake_subcommand(sys.argv[2:])
        return

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    parser = get_arg_parser(func_name)
    args, nested_args = parser.parse_known_args()

    do_log_args = func_name != "do_print_balances"
    if do_log_args:
        print_args(args, nested_args)

    func(args, nested_args)


# ========================================================================
# actual cli implementations. Given in same order as HELP_LONG


# do_help() is implemented in cli_arguments and imported, so nothing needed here


@enforce_types
def do_sim(args, nested_args=None):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network="development",
        nested_override_args=nested_args,
    )
    feedset = ppss.predictoor_ss.predict_train_feedsets[0]
    if len(ppss.predictoor_ss.predict_train_feedsets) > 0:
        logger.warning("Multiple predict feeds provided, using the first one")
    sim_engine = SimEngine(ppss, feedset)
    sim_engine.run()


@enforce_types
# pylint: disable=unused-argument
def do_predictoor(args, nested_args=None):
    ppss = args.PPSS
    agent = PredictoorAgent(ppss)
    agent.run()


@enforce_types
# pylint: disable=unused-argument
def do_trader(args, nested_args=None):
    ppss = args.PPSS
    approach = args.APPROACH

    if approach == 1:
        agent = TraderAgent1(ppss)
    elif approach == 2:
        agent = TraderAgent2(ppss)
    else:
        raise ValueError(f"Unknown trader approach {approach}")

    agent.run()


@enforce_types
def do_claim_OCEAN(args, nested_args=None):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network="sapphire-mainnet",
        nested_override_args=nested_args,
    )
    do_ocean_payout(ppss)


@enforce_types
def do_claim_ROSE(args, nested_args=None):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network="sapphire-mainnet",
        nested_override_args=nested_args,
    )
    do_rose_payout(ppss)


@enforce_types
def do_multisim(args, nested_args=None):
    d = PPSS.constructor_dict(
        yaml_filename=args.PPSS_FILE,
        nested_override_args=nested_args,
    )
    multisim_engine = MultisimEngine(d=d)
    multisim_engine.run()


@enforce_types
# pylint: disable=unused-argument
def do_deployer(args, nested_args=None):
    deployer_main(args)


@enforce_types
# pylint: disable=unused-argument
def do_ohlcv(args, nested_args=None):
    ppss = args.PPSS
    ohlcv_data_factory = OhlcvDataFactory(ppss.lake_ss)
    df = ohlcv_data_factory.get_mergedohlcv_df()
    print(df)


@enforce_types
# pylint: disable=unused-argument
def do_get_predictoors_info(args, nested_args=None):
    """
    @description
        The following args are post-lake filters:
        ST = Start time string (e.g. "2021-01-01")
        END = End time string (e.g. "2022-01-01")
        PDRS = List of predictoor addresses to filter on (e.g. ["0x1", "0x2"])
    """
    ppss = args.PPSS
    pdrs = args.PDRS or []
    get_predictoors_info_main(ppss, args.ST, args.END, pdrs)


@enforce_types
# pylint: disable=unused-argument
def do_get_predictions_info(args, nested_args=None):
    """
    @description
        The following args are post-lake filters:
        ST = Start time string (e.g. "2021-01-01")
        END = End time string (e.g. "2022-01-01")
        PDRS = List of feed addresses to filter on (e.g. ["0x1", "0x2"])
    """
    ppss = args.PPSS
    feeds = args.FEEDS or []
    get_predictions_info_main(ppss, args.ST, args.END, feeds)


@enforce_types
# pylint: disable=unused-argument
def do_get_traction_info(args, nested_args=None):
    """
    @description
        PQDIR = overrides lake parquet dir

        The following args are post-lake filters:
        ST = Start time string (e.g. "2021-01-01")
        END = End time string (e.g. "2022-01-01")
    """
    ppss = args.PPSS
    ppss.lake_ss.d["lake_dir"] = args.PQDIR
    get_traction_info_main(ppss, args.ST, args.END)


@enforce_types
# pylint: disable=unused-argument
def do_check_network(args, nested_args=None):
    ppss = args.PPSS
    check_network_main(ppss, args.LOOKBACK_HOURS)


@enforce_types
# pylint: disable=unused-argument
def do_trueval(args, nested_args=None, testing=False):
    ppss = args.PPSS
    predictoor_batcher_addr = ppss.web3_pp.get_address("PredictoorHelper")
    agent = TruevalAgent(ppss, predictoor_batcher_addr)

    agent.run(testing)


@enforce_types
# pylint: disable=unused-argument
def do_dfbuyer(args, nested_args=None):
    ppss = args.PPSS
    agent = DFBuyerAgent(ppss)
    agent.run()


@enforce_types
# pylint: disable=unused-argument
def do_publisher(args, nested_args=None):
    ppss = args.PPSS

    if ppss.web3_pp.network == "development":
        fund_accounts_with_OCEAN(ppss.web3_pp)
    publish_assets(ppss.web3_pp, ppss.publisher_ss)


@enforce_types
# pylint: disable=unused-argument
def do_topup(args, nested_args=None):
    ppss = args.PPSS
    topup_main(ppss)


@enforce_types
# pylint: disable=unused-argument
def do_create_accounts(args, nested_args=None):
    create_accounts(args.NUM)


@enforce_types
# pylint: disable=unused-argument
def do_print_balances(args, nested_args=None):
    ppss = args.PPSS
    account = args.ACCOUNT
    print_balances(account, ppss.web3_pp)


@enforce_types
# pylint: disable=unused-argument
def do_fund_accounts(args, nested_args=None):
    ppss = args.PPSS
    to_accounts = args.ACCOUNTS
    fund_accounts(Eth(args.TOKEN_AMOUNT), to_accounts, ppss.web3_pp, args.NATIVE_TOKEN)


@enforce_types
# pylint: disable=unused-argument
def do_deploy_pred_submitter_mgr(args, nested_args=None):
    ppss = args.PPSS
    contract_address = deploy_pred_submitter_mgr_contract(ppss.web3_pp)
    logger.info(
        "Prediction Submitter Manager Contract deployed at %s", contract_address
    )


@enforce_types
# pylint: disable=unused-argument
def do_sim_plots(args, nested_args=None):
    sim_dash(args)


@enforce_types
# pylint: disable=unused-argument
def do_arima_plots(args, nested_args=None):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network="development",
        nested_override_args=nested_args,
    )
    arima_dash(ppss, args.debug_mode)


@enforce_types
# pylint: disable=unused-argument
def do_predictoor_dashboard(args, nested_args=None):
    predictoor_dash(args.PPSS, args.debug_mode)
