import os
from unittest.mock import Mock, call

from enforce_typing import enforce_types
from eth_account import Account

from pdr_backend.contract.token import Token
from pdr_backend.ppss.web3_pp import mock_web3_pp
from pdr_backend.util.fund_accounts import fund_accounts, fund_core_accounts_with_OCEAN


@enforce_types
def test_fund_accounts_with_OCEAN(monkeypatch):
    web3_pp = mock_web3_pp("development")

    path = "pdr_backend.util.fund_accounts"

    monkeypatch.setattr(f"{path}.get_address", Mock())
    monkeypatch.setattr(f"{path}.Token", Mock())

    mock_f = Mock()
    monkeypatch.setattr(f"{path}.fund_accounts", mock_f)

    fund_core_accounts_with_OCEAN(web3_pp)
    mock_f.assert_called()


@enforce_types
def test_fund_accounts(monkeypatch):
    pk = os.getenv("PRIVATE_KEY")
    monkeypatch.setenv("PREDICTOOR_PRIVATE_KEY", pk)
    monkeypatch.setenv("PREDICTOOR2_PRIVATE_KEY", pk)

    mock_token = Mock(spec=Token)
    mock_account = Mock(spec=str)

    accounts_to_fund = [
        ("PREDICTOOR_PRIVATE_KEY", 2000),
        ("PREDICTOOR2_PRIVATE_KEY", 3000),
    ]

    fund_accounts(accounts_to_fund, mock_account, mock_token)

    a = Account.from_key(private_key=pk)  # pylint: disable=no-value-for-parameter
    mock_token.transfer.assert_has_calls(
        [
            call(a.address, 2e21, mock_account),
            call(a.address, 3e21, mock_account),
        ]
    )
