from pdr_backend.trader.trader_agent import TraderAgent, trade
from pdr_backend.trader.trader_config import TraderConfig


def main(testing=False):
    config = TraderConfig()
    t = TraderAgent(config, trade)
    t.run(testing)


if __name__ == "__main__":
    main()
