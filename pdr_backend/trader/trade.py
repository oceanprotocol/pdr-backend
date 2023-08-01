"""
Flow
  FIMXE

Notes on customization:
  FIXME
"""


def trade(topic, direction):
    """Given a direction for a topic, let's trade
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
        f" {topic['name']} (contract {topic['address']}) has a new prediction: {direction}.  Let's buy or sell"
    )
    """  Do your things here """
