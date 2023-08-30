from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.trueval.trueval_agent import TruevalAgent, get_trueval


def main(testing=False):
    config = TruevalConfig()
    t = TruevalAgent(config, get_trueval)
    t.run(testing)


if __name__ == "__main__":
    main()
