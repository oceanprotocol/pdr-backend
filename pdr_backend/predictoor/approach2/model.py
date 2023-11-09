import sys

sys.path.append("../")
import pandas as pd
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix as cm
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold
import copy
import pickle


class OceanModel:
    def __init__(self, exchange, pair, timeframe):
        self.model_name = self.__class__.__name__
        self.model = None
        self.exchange = exchange.lower()
        self.pair = pair.replace("/", "-").lower()
        self.timeframe = timeframe
        self.predictor = LinearDiscriminantAnalysis()

    def feature_extraction(self, dataframe):
        return dataframe[["close"]]

    def format_train_data(self, path):
        data = pd.read_csv(path)
        data = data.set_index("timestamp")
        data.index = pd.to_datetime(data.index, utc=True).tz_convert(None)
        mindate = pd.to_datetime("2019-01-01", utc=True).tz_convert(None)
        data = data.iloc[data.index > mindate, :]

        freqstr = self.timeframe[:-1] + "T"
        data = data.asfreq(freqstr)
        data = data[["close"]]

        data = self.feature_extraction(data)
        data["labels"] = np.where(data["close"].diff().shift(-1) > 0, 1, 0)
        data["returns"] = data["close"].diff().shift(-1) / data["close"]
        data = data.dropna()

        x = data.drop(["labels", "returns"], axis=1).values
        y = data["labels"].values
        r = data["returns"].values

        return x, y, r

    def format_test_data(self, dataframe):
        dataframe = self.feature_extraction(dataframe)
        dataframe = dataframe.dropna()
        return dataframe

    def train_from_csv(self, path):
        x, y, r = self.format_train_data(path)
        self.train(x, y, r)

    def train(self, x, y, r):
        if self.predictor is None:
            raise Exception("Division by zero is not allowed.")

        print("creating model")
        self.model = Pipeline(
            steps=[
                ("Predictor", self.predictor),
            ]
        )
        self.model.fit(x, y)

    def predict(self, last_candles):
        dataframe = copy.deepcopy(last_candles)
        dataframe = self.feature_extraction(dataframe)
        prob = self.model.predict_proba(dataframe.values[[-1], :])[0]
        yhat = self.model.predict(dataframe.values[[-1], :])[0]
        return yhat, prob[yhat]

    def back_test_crossval(self, nfolds, path):
        model = Pipeline(
            steps=[
                ("Predictor", self.predictor),
            ]
        )

        x, y, r = self.format_train_data(path)

        kf = KFold(n_splits=nfolds)
        pred_returns = np.zeros((nfolds,))
        opt_returns = np.zeros((nfolds,))
        timeframes = np.zeros((nfolds,))
        ACC = np.zeros((nfolds,))
        conf_mat = np.zeros((2, 2))
        for i, (ind_train, ind_test) in enumerate(kf.split(x)):
            model.fit(x[ind_train, :], y[ind_train])
            yhat = model.predict(x[ind_test, :])
            sample_weight_test = np.abs(r[ind_test])
            ACC[i] = model.score(x[ind_test, :], y[ind_test])
            conf_mat += cm(y[ind_test], yhat)
            pred_returns[i] = np.sum(r[ind_test][yhat == 1])
            opt_returns[i] = np.sum(r[ind_test][y[ind_test] == 1])
            timeframes[i] = ind_test.shape[0]

        # returns:
        # mean of predicted_returns across folds
        # mean of returns using a perfect oracle for predictions
        # average number of smaples per fold
        # average accuracy
        # confusion matrix
        return (
            np.mean(pred_returns),
            np.mean(opt_returns),
            np.mean(timeframes),
            np.mean(ACC),
            conf_mat,
        )

    def pickle_model(self, path):
        model_name = (
            path
            + "/"
            + self.model_name
            + "_"
            + self.exchange
            + "_"
            + self.pair
            + "_"
            + self.timeframe
            + ".pkl"
        )
        with open(model_name, "wb") as f:
            pickle.dump(self.model, f)

    def unpickle_model(self, path):
        model_name = (
            path
            + "/"
            + self.model_name
            + "_"
            + self.exchange
            + "_"
            + self.pair
            + "_"
            + self.timeframe
            + ".pkl"
        )
        with open(model_name, "rb") as f:
            self.model = pickle.load(f)