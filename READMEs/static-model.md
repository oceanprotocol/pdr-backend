<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Run Static Model Predictoor

The default flow for predictoors is approach3: dynamically building models.

_This_ README is for approach2, which uses static models. Static models are developed and saved in a different repo.

NOTE: this approach may be deprecated in the future.

There are two macro steps:
1. [Develop & backtest static models](#develop-and-backtest-models)
1. [Use model in Predictoor bot](#use-model-in-predictoor-bot)

The first step is done in a _separate_ repo.

Let's go through each step in turn.

## Develop and backtest models

Normally you'd have to develop your own model.

However to get you going, we've developed a simple model, at [`pdr-model-simple`](https://github.com/oceanprotocol/pdr-model-simple) repo.

The second step will show how to connect this model to the bot.

## Use model in Predictoor bot

The bot itself will run from [`predictoor/approach2/main.py`](../pdr_backend/predictoor/approach2/main.py), using `predict.py` in the same dir. That bot needs to sees the model developed elsewhere.

Here's how to get everything going.

In work console:
```console
# go to a directory where you'll want to clone to. Here's one example.
cd ~/code/ 

#clone model repo
git clone https://github.com/oceanprotocol/pdr-model-simple

#the script below needs this envvar, to know where to import model.py from
export MODELDIR=$(pwd)/pdr-model-simple/

#pip install anything that pdr-model-simple/model.py needs
pip install scikit-learn ta

#run static model predictoor bot
python pdr_backend/predictoor/main.py 2
```

## Your own static model

Once you're familiar with the above, you can make your own model: fork `pdr-model-simple` and change it as you wish. Finally, link your predictoor bot to your new model repo, like shown above.

## Other READMEs

- [Parent predictoor README: predictoor.md](./predictoor.md)
- [Root README](../README.md)
