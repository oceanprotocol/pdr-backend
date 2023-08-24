from typing import List
from pdr_backend.util.subgraph import query_subgraph


def query_pending_payouts(addr: str) -> List[int]:
    chunk_size = 1000
    offset = 0
    timestamps: List[int] = []

    while True:
        query = """
        {
                predictPredictions(
                    where: {user: "%s", payout: null}
                ) {
                    id
                    timestamp
                }
        }
        """ % (addr)

        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            if not "data" in result:
                print("No data in result")
                break
            predict_predictions = result["data"]["predictPredictions"]
            timestamps_query = [i["timestamp"] for i in predict_predictions]
            timestamps.extend(timestamps_query)
        except Exception as e:
            print("An error occured", e)

    return timestamps