from os import name
import pytest
from unittest.mock import MagicMock, patch

from pdr_backend.models.token import NativeToken, Token
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.topup import topup_main


@pytest.fixture(name="mock_ppss_")
def mock_ppss(tmpdir):
    web3_config = MagicMock()
    web3_config.w3.eth = MagicMock()
    web3_config.w3.eth.chain_id = 23294

    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = MagicMock()
    ppss.web3_pp.web3_config = web3_config
    return ppss


@pytest.fixture(name="mock_token_")
def mock_token():
    token = MagicMock(spec=Token)
    token.balanceOf.side_effect = [500 * 1e18, 0, 0]  # Mock balance in wei
    token.transfer.return_value = None
    return token


@pytest.fixture(name="mock_native_token_")
def mock_native_token():
    native_token = MagicMock(spec=NativeToken)
    native_token.balanceOf.side_effect = [500 * 1e18, 0, 0]  # Mock balance in wei
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


def test_topup_main(
    mock_ppss_, mock_token_, mock_native_token_, mock_get_opf_addresses_
):
    with patch("pdr_backend.util.topup.Token", return_value=mock_token_), patch(
        "pdr_backend.util.topup.NativeToken", return_value=mock_native_token_
    ), patch(
        "pdr_backend.util.topup.get_opf_addresses", mock_get_opf_addresses_
    ), patch(
        "pdr_backend.util.topup.sys.exit"
    ) as mock_exit:
        topup_main(mock_ppss_)

        mock_exit.assert_called_with(0)

        assert mock_token_.transfer.called
        assert mock_native_token_.transfer.called
