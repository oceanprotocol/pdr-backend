def predict_function(topic, estimated_time, model, main_pd):
    """Given a topic, let's predict
    Topic object looks like:

    {
        "name":"ETH-USDT",
        "address":"0x54b5ebeed85f4178c6cb98dd185067991d058d55",
        "symbol":"ETH-USDT",
        "blocks_per_epoch":"60",
        "blocks_per_subscription":"86400",
        "last_submited_epoch":0,
        "pair":"eth-usdt",
        "base":"eth",
        "quote":"usdt",
        "source":"kraken",
        "timeframe":"5m"
    }

    """
    print(
        f" We were asked to predict {topic['name']} "
        f"(contract: {topic['address']}) value "
        f"at estimated timestamp: {estimated_time}"
    )
    predicted_confidence = None
    predicted_value = None

    try:
        predicted_value, predicted_confidence = model.predict(main_pd)
        predicted_value = bool(predicted_value)
        print(
            f"Predicting {predicted_value} with a confidence of {predicted_confidence}"
        )

    except Exception as e:
        print(e)

    return (predicted_value, predicted_confidence)
