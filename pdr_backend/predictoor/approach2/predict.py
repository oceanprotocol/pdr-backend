def get_prediction(feed: dict, timestamp: str, model, main_pd):
    print(
        f" We were asked to predict {feed['name']} "
        f"(contract: {feed['address']}) value "
        f"at estimated timestamp: {timestamp}"
    )
    predval, stake = None, None

    try:
        predval, stake = model.predict(main_pd)
        predval = bool(predval)
        print(f"Predicting {predval} with stake {stake}")

    except Exception as e:
        print(e)

    return (predval, stake)
