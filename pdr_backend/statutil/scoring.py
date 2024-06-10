from enforce_typing import enforce_types

import numpy as np


@enforce_types
def classif_acc(ytrue_hat, ytrue) -> float:
    ytrue_hat, ytrue = np.array(ytrue_hat), np.array(ytrue)
    n_correct = sum(ytrue_hat == ytrue)
    acc = n_correct / len(ytrue)
    return acc
