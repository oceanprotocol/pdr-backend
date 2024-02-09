from unittest.mock import MagicMock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.mathutil import to_wei
from pdr_backend.util.topup import topup_main


@pytest.fixture(name="mock_token_")
def mock_token():
    token = MagicMock(spec=Token)
    token.balanceOf.side_effect = [
        to_wei(500),
        to_wei(500),
        0,
        0,
        0,
        0,
    ]  # Mock balance in wei
    token.transfer.return_value = None
    return token


@pytest.fixture(name="mock_native_token_")
def mock_native_token():
    native_token = MagicMock(spec=NativeToken)
    native_token.balanceOf.side_effect = [
        to_wei(500),
        to_wei(500),
        0,
        0,
        0,
        0,
    ]  # Mock balance in wei
    native_token.transfer.return_value = None
    return native_token


@pytest.fixture(name="mock_get_opf_addresses_")
def mock_get_opf_addresses():
    return MagicMock(
        return_value={
            "predictoor1": "0x1",
            "predictoor2": "0x2",
        }
    )


@enforce_types
def test_topup_main(mock_token_, mock_native_token_, mock_get_opf_addresses_, tmpdir):
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet", str(tmpdir))

    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-testnet"
    mock_web3_pp.OCEAN_Token = mock_token_
    mock_web3_pp.NativeToken = mock_native_token_

    ppss.web3_pp = mock_web3_pp

    topup_ss = MagicMock()
    topup_ss.all_topup_addresses = mock_get_opf_addresses_
    topup_ss.get_min_bal.side_effect = [20, 30, 20, 30]
    topup_ss.get_topup_bal.side_effect = [20, 30, 20, 30]
    ppss.topup_ss = topup_ss

    PATH = "pdr_backend.util.topup"
    with patch(f"{PATH}.sys.exit") as mock_exit:
        topup_main(ppss)

        mock_exit.assert_called_with(0)

        assert mock_token_.transfer.called
        assert mock_native_token_.transfer.called
