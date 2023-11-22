import csv
import os
from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.subgraph import query_subgraph

addresses = {
    "predictoor1": "0x35Afee1168D1e1053298F368488F4eE95E891a6e",
    "predictoor2": "0x1628BeA0Fb859D56Cd2388054c0bA395827e4374",
    "predictoor3": "0x3f0825d0c0bbfbb86cd13C7E6c9dC778E3Bb44ec",
    "predictoor4": "0x20704E4297B1b014d9dB3972cc63d185C6C00615",
    "predictoor5": "0xf38426BF6c117e7C5A6e484Ed0C8b86d4Ae7Ff78",
    "predictoor6": "0xFe4A9C5F3A4EA5B1BfC089713ed5fce4bB276683",
    "predictoor7": "0x078F083525Ad1C0d75Bc7e329EE6656bb7C81b12",
    "predictoor8": "0x4A15CC5C20c5C5F71A9EA6376356f72b2A760f12",
    "predictoor9": "0xD2a24CB4ff2584bAD80FF5F109034a891c3d88dD",
    "predictoor10": "0x8a64CF23B5BB16Fd7444B47f94673B90Cc0F75cE",
    "predictoor11": "0xD15749B83Be987fEAFa1D310eCc642E0e24CadBA",
    "predictoor12": "0xAAbDBaB266b31d6C263b110bA9BE4930e63ce817",
    "predictoor13": "0xB6431778C00F44c179D8D53f0E3d13334C051bd3",
    "predictoor14": "0x2c2C599EC040F47C518fa96D08A92c5df5f50951",
    "predictoor15": "0x5C72F76F7dae16dD34Cb6183b73F4791aa4B3BC4",
    "predictoor16": "0x19C0A543664F819C7F9fb6475CE5b90Bfb112d26",
    "predictoor17": "0x8cC3E2649777d59809C8d3E2Dd6E90FDAbBed502",
    "predictoor18": "0xF5F2a495E0bcB50bF6821a857c5d4a694F5C19b4",
    "predictoor19": "0x4f17B06177D37E24158fec982D48563bCEF97Fe6",
    "predictoor20": "0x784b52987A894d74E37d494F91eD03a5Ab37aB36",
}


predictoor_pairs = {
    "predictoor1": {"pair": "BTC", "timeframe": "5m"},
    "predictoor2": {"pair": "BTC", "timeframe": "1h"},
    "predictoor3": {"pair": "ETH", "timeframe": "5m"},
    "predictoor4": {"pair": "ETH", "timeframe": "1h"},
    "predictoor5": {"pair": "BNB", "timeframe": "5m"},
    "predictoor6": {"pair": "BNB", "timeframe": "1h"},
    "predictoor7": {"pair": "XRP", "timeframe": "5m"},
    "predictoor8": {"pair": "XRP", "timeframe": "1h"},
    "predictoor9": {"pair": "ADA", "timeframe": "5m"},
    "predictoor10": {"pair": "ADA", "timeframe": "1h"},
    "predictoor11": {"pair": "DOGE", "timeframe": "5m"},
    "predictoor12": {"pair": "DOGE", "timeframe": "1h"},
    "predictoor13": {"pair": "SOL", "timeframe": "5m"},
    "predictoor14": {"pair": "SOL", "timeframe": "1h"},
    "predictoor15": {"pair": "LTC", "timeframe": "5m"},
    "predictoor16": {"pair": "LTC", "timeframe": "1h"},
    "predictoor17": {"pair": "TRX", "timeframe": "5m"},
    "predictoor18": {"pair": "TRX", "timeframe": "1h"},
    "predictoor19": {"pair": "DOT", "timeframe": "5m"},
    "predictoor20": {"pair": "DOT", "timeframe": "1h"},
}


@enforce_types
class SimplePrediction:  # maybe TODO: replace with model.prediction.Prediction
    def __init__(self, pair, timeframe, predval, stake, trueval, timestamp) -> None:
        self.pair: str = pair
        self.timeframe: str = timeframe
        self.predval = predval
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp


@enforce_types
def get_all_predictions(ppss) -> List[SimplePrediction]:
    chunk_size: int = 1000
    offset: int = 0
    all_pred_objs: List[SimplePrediction] = []

    address_filter: List[str] = [a.lower() for a in addresses.values()]

    while True:
        query = """
            {
            predictPredictions(skip: %s, first: %s, where: {user_: {id_in: %s}}) {
                id
                user {
                    id
                }
                stake
                payout {
                    payout
                    trueValue
                    predictedValue
                }
                slot {
                    slot
                }
            }
            }
        """ % (
            offset,
            chunk_size,
            str(address_filter).replace("'", '"'),
        )

        result = query_subgraph(
            ppss.web3_pp.subgraph_url,
            query,
            timeout=10.0,
        )

        print(".")

        offset += 1000

        if not "data" in result:
            break

        result_data = result["data"]["predictPredictions"]
        if len(result_data) == 0:
            break
        for pred_dict in result_data:
            pdr_key = [
                key
                for key, address in addresses.items()
                if address.lower() == pred_dict["user"]["id"]
            ][0]
            pair_info = predictoor_pairs[pdr_key]
            pair_name = pair_info["pair"]
            timeframe = pair_info["timeframe"]
            timestamp = pred_dict["slot"]["slot"]

            if pred_dict["payout"] is None:
                continue

            trueval = pred_dict["payout"]["trueValue"]
            if trueval is None:
                continue

            predval = pred_dict["payout"]["predictedValue"]

            stake = float(pred_dict["stake"])
            if stake < 0.01:
                continue

            pred_obj = SimplePrediction(
                pair_name, timeframe, predval, stake, trueval, timestamp
            )
            all_pred_objs.append(pred_obj)

    return all_pred_objs


@enforce_types
def _group_preds_by_pair_timeframe(all_pred_objs: List[SimplePrediction]):
    """Return a dict of [pair_timeframe] : List[SimplePrediction]"""
    d: Dict[str, List[SimplePrediction]] = {}
    for pred_obj in all_pred_objs:
        k = _pair_timeframe(pred_obj)
        if k not in d:
            d[k] = []
        d[k].append(pred_obj)
    return d


@enforce_types
def _pair_timeframe(pred_obj: SimplePrediction) -> str:
    """Returns e.g. "BTC/ETH_5m" for a given pred_obj"""
    return f"{pred_obj.pair}_{pred_obj.timeframe}"


@enforce_types
def write_csv(all_pred_objs: List[SimplePrediction], csvdir: str):
    preds_dict = _group_preds_by_pair_timeframe(all_pred_objs)

    for pair_timeframe, pred_objs in preds_dict.items():
        pred_objs.sort(pair_timeframe=lambda x: x.timestamp)

        filebase = pair_timeframe + ".csv"
        filename = os.path.abspath(os.path.join(csvdir, filebase))
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Predicted Value", "True Value", "Timestamp", "Stake"])
            for pred_obj in pred_objs:
                writer.writerow(
                    [
                        pred_obj.predval,
                        pred_obj.trueval,
                        pred_obj.timestamp,
                        pred_obj.stake,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")


@enforce_types
def get_opf_predictions_main(ppss: PPSS, csvdir: str):
    all_pred_objs: List[SimplePrediction] = get_all_predictions(ppss)
    write_csv(all_pred_objs, csvdir)
