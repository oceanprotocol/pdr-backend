
def main(testing=False):
    config = TraderConfig()
    t = TraderAgent(config)
    t.run(testing)


if __name__ == "__main__":
    main()
