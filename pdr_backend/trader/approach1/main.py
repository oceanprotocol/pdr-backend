from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach1.trader_config1 import TraderConfig1


def main(testing=False):
    config = TraderConfig1()
    t = TraderAgent1(config)
    t.run(testing)


if __name__ == "__main__":
    main()
