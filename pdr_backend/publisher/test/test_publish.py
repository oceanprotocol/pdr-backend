import os
from unittest.mock import Mock, call

from eth_account import Account

from pdr_backend.models.token import Token
from pdr_backend.publisher.publish import fund_dev_accounts


def test_fund_dev_accounts(monkeypatch):
    pk = os.getenv("PRIVATE_KEY")
    monkeypatch.setenv("PREDICTOOR_PRIVATE_KEY", pk)
    monkeypatch.setenv("PREDICTOOR2_PRIVATE_KEY", pk)

    mock_token = Mock(spec=Token)
    mock_account = Mock(spec=str)

    accounts_to_fund = [
        ("PREDICTOOR_PRIVATE_KEY", 2000),
        ("PREDICTOOR2_PRIVATE_KEY", 3000),
    ]

    fund_dev_accounts(accounts_to_fund, mock_account, mock_token)

    a = Account.from_key(private_key=pk)  # pylint: disable=no-value-for-parameter
    mock_token.transfer.assert_has_calls(
        [
            call(a.address, 2e21, mock_account),
            call(a.address, 3e21, mock_account),
        ]
    )
