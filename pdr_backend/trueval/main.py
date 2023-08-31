from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.publisher.publish import add_erc20_deployer
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.trueval_agent import TruevalAgent, get_trueval
from pdr_backend.util.contract import get_address


def main(testing=False):
    config = TruevalConfig()
    predictoor_batcher_addr = "0x74b3d397BF809b40E2A686BD6c1116453399A66E"

    t = TruevalAgentBatch(config, get_trueval, predictoor_batcher_addr)

    t.run(testing)


if __name__ == "__main__":
    main()


# pk1: 0x46cc668ff7302ad475fefc45716dd73217fdd8b65256d73362597e0f4a9c6c97
# pk2: other : 0x6fb6d4384a16a0b50afce957faf48582e3ca82f3c6796dd8ec78ad53d73043be

# 0xE02A421dFc549336d47eFEE85699Bd0A3Da7D6FF

# 0x005FD44e007866508f62b04ce9f43dd1d36D0c0c
