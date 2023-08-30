from unittest.mock import Mock, call

from eth_account import Account

from pdr_backend.models.token import Token
from pdr_backend.publisher.publish import fund_dev_accounts


def test_fund_dev_accounts(monkeypatch):
    pk = "0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"
    monkeypatch.setenv("PREDICTOOR_PRIVATE_KEY", pk)
    monkeypatch.setenv("PREDICTOOR2_PRIVATE_KEY", pk)

    mock_token = Mock(spec=Token)
    mock_account = Mock(spec=str)

    accounts_to_fund = [
        ("PREDICTOOR_PRIVATE_KEY", 2000),
        ("PREDICTOOR2_PRIVATE_KEY", 3000),
    ]

    fund_dev_accounts(accounts_to_fund, mock_account, mock_token)

    mock_token.transfer.assert_has_calls(
        [
            call("0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e", 2e21, mock_account),
            call("0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e", 3e21, mock_account),
        ]
    )
