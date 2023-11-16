import argparse
import os

from enforce_typing import enforce_types

# ========================================================================
HELP_LONG = """Predictoor tool

Usage: pdr sim|predictoor|trader|..

  pdr sim [YAML_FILE]
  pdr predictoor 1|2|3 <network> [YAML_FILE]
  pdr trader 1|2 <network> [YAML_FILE]
  pdr claim OCEAN|ROSE
  pdr help - full command list

Transactions are signed with envvar 'PRIVATE_KEY`.
<network> may be: sapphire-testnet|sapphire-mainnet|barge-pdr|barge-pytest
If no YAML_FILE given, it uses ppss.yaml.

For core team:
  pdr dfbuyer [YAML_FILE]
  pdr publisher [YAML_FILE]
  pdr trueval [YAML_FILE]
"""


@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)


