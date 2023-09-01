from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.trueval_agent import TruevalAgent, get_trueval
from pdr_backend.util.contract import get_address


def main(testing=False):
    config = TruevalConfig()
    predictoor_batcher_addr = get_address("PredictoorHelper")
    t = TruevalAgentBatch(config, get_trueval, predictoor_batcher_addr)
    t.run(testing)


if __name__ == "__main__":
    main()
