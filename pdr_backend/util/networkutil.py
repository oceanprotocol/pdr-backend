#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import requests
from enforce_typing import enforce_types

logger = logging.getLogger("cli")


@enforce_types
def get_sapphire_postfix(network: str) -> str:
    if network == "sapphire-testnet":
        return "testnet"
    if network == "sapphire-mainnet":
        return "mainnet"

    raise ValueError(f"'{network}' is not valid name")


@enforce_types
def get_subgraph_url(network: str) -> str:
    """
    Returns the subgraph URL for the given network.

    Args:
        network (str): The network name ("mainnet" or "testnet").

    Returns:
        str: The subgraph URL for the specified network.
    """
    if network not in ["mainnet", "testnet"]:
        raise ValueError(
            "Invalid network. Acceptable values are 'mainnet' or 'testnet'."
        )

    # pylint: disable=line-too-long
    return f"https://v4.subgraph.sapphire-{network}.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"


@enforce_types
def download_file(url: str, file_path: str, timeout: int = 10):
    """
    Downloads a file from a given URL and saves it to
    the specified file path.
    
    Args:
        url (str): The URL of the file to download.
        file_path (str): The local path where the file will be saved.
        timeout (int, optional): The maximum number of seconds 
        to wait for a response from the server. Defaults to 10.
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)

        # Check if the request was successful (status code 200)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(file_path, "wb") as file:
            for data in response.iter_content(chunk_size=1024):
                downloaded += len(data)
                file.write(data)

                # Print basic progress information
                percent_done = (downloaded / total_size) * 100 if total_size else 0
                logger.info("Download progress: %.2f%%", percent_done)

        logger.info("File downloaded successfully to %s", file_path)

    except requests.Timeout:
        logger.error("Timeout occurred while trying to download %s", url)
    except requests.RequestException as e:
        logger.error("An error occurred: %s", e)
