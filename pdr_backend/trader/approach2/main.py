from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trader.approach2.trader_config2 import TraderConfig2


def main(testing=False):
    config = TraderConfig2()
    t = TraderAgent2(config)
    t.run(testing)


if __name__ == "__main__":
    main()
