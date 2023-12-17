from unittest.mock import MagicMock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.models.token import NativeToken, Token
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.util.mathutil import to_wei
from pdr_backend.util.topup import topup_main


@pytest.fixture(name="mock_token_")
def mock_token():
    token = MagicMock(spec=Token)
    token.balanceOf.side_effect = [to_wei(500), 0, 0]  # Mock balance in wei
    token.transfer.return_value = None
    return token


@pytest.fixture(name="mock_native_token_")
def mock_native_token():
    native_token = MagicMock(spec=NativeToken)
    native_token.balanceOf.side_effect = [to_wei(500), 0, 0]  # Mock balance in wei
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
    ppss = mock_ppss("5m", ["binance c BTC/USDT"], "sapphire-mainnet", str(tmpdir))

    PATH = "pdr_backend.util.topup"
    with patch(f"{PATH}.Token", return_value=mock_token_), patch(
        f"{PATH}.NativeToken", return_value=mock_native_token_
    ), patch(f"{PATH}.get_opf_addresses", mock_get_opf_addresses_), patch(
        f"{PATH}.sys.exit"
    ) as mock_exit:
        topup_main(ppss)

        mock_exit.assert_called_with(0)

        assert mock_token_.transfer.called
        assert mock_native_token_.transfer.called
