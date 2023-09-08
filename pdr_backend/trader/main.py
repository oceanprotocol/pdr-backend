from pdr_backend.trader.trader_agent import TraderAgent, get_trader
from pdr_backend.trader.trader_config import TraderConfig


def main(testing=False):
    config = TraderConfig()
    t = TraderAgent(config, get_trader)
    t.run(testing)


if __name__ == "__main__":
    main()
