import time
from typing import Dict

import requests
from enforce_typing import enforce_types

from pdr_backend.util.constants import SUBGRAPH_MAX_TRIES


@enforce_types
def query_subgraph(
    subgraph_url: str, query: str, tries: int = 3, timeout: float = 30.0
) -> Dict[str, dict]:
    """
    @arguments
      subgraph_url -- e.g. http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph # pylint: disable=line-too-long
      query -- e.g. in docstring above

    @return
      result -- e.g. {"data" : {"predictContracts": ..}}
    """
    response = requests.post(subgraph_url, "", json={"query": query}, timeout=timeout)
    if response.status_code != 200:
        # pylint: disable=broad-exception-raised
        if tries < SUBGRAPH_MAX_TRIES:
            time.sleep(((tries + 1) / 2) ** (2) * 10)
            return query_subgraph(subgraph_url, query, tries + 1)

        raise Exception(
            f"Query failed. Url: {subgraph_url}. Return code is {response.status_code}\n{query}"
        )

    result = response.json()

    return result
