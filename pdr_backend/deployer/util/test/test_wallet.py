from unittest.mock import patch, MagicMock
from pdr_backend.deployer.util.wallet import (
    Wallet,
    generate_wallet,
    generate_wallets,
    read_keys_json,
    generate_new_keys,
)


def test_wallet():
    wallet = Wallet("private_key")
    assert str(wallet) == "private_key"


@patch("pdr_backend.deployer.util.wallet.Web3")
def test_generate_wallet(mock_web3):
    mock_web3_instance = MagicMock()
    mock_web3.return_value = mock_web3_instance
    mock_account = mock_web3_instance.eth.account.create.return_value
    mock_account._private_key.hex.return_value = "private_key"
    wallet = generate_wallet()
    assert wallet.private_key == "private_key"
    mock_web3_instance.eth.account.create.assert_called_once()


@patch("pdr_backend.deployer.util.wallet.generate_wallet")
def test_generate_wallets(mock_generate_wallet):
    mock_generate_wallet.return_value = Wallet("private_key")
    wallets = generate_wallets(3)
    assert len(wallets) == 3
    assert all(wallet.private_key == "private_key" for wallet in wallets)
    assert mock_generate_wallet.call_count == 3


@patch("pdr_backend.deployer.util.wallet.os.path.exists")
@patch("pdr_backend.deployer.util.wallet.json.load")
def test_read_keys_json(mock_json_load, mock_os_path_exists):
    mock_os_path_exists.return_value = True
    mock_json_load.return_value = {"config": ["private_key1", "private_key2"]}
    wallets = read_keys_json("config")
    assert len(wallets) == 2
    assert wallets[0].private_key == "private_key1"
    assert wallets[1].private_key == "private_key2"


@patch("pdr_backend.deployer.util.wallet.generate_wallets")
@patch("pdr_backend.deployer.util.wallet.read_keys_json")
@patch("pdr_backend.deployer.util.wallet.json.dump")
def test_generate_new_keys(mock_json_dump, mock_read_keys_json, mock_generate_wallets):
    mock_read_keys_json.return_value = [Wallet("private_key1")]
    mock_generate_wallets.return_value = [Wallet("private_key2")]
    wallets = generate_new_keys("config", 1)
    assert len(wallets) == 2
    assert wallets[0].private_key == "private_key1"
    assert wallets[1].private_key == "private_key2"
    mock_json_dump.assert_called_once()
