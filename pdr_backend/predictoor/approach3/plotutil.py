import matplotlib
import matplotlib.pyplot as plt
import numpy as np

HEIGHT = 8
WIDTH = HEIGHT * 2

def plot_vals_vs_time1(y, yhat, title=""):
    matplotlib.rcParams.update({"font.size": 22})
    assert len(y) == len(yhat)
    N = len(y)
    x = [h for h in range(0, N)]
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.plot(x, y, "g-", label="y")
    ax.plot(x, yhat, "b-", label="yhat")
    ax.legend(loc="lower right")
    plt.ylabel("y")
    plt.xlabel("time")
    fig.set_size_inches(WIDTH, HEIGHT)
    plt.show()
    
def plot_vals_vs_time2(y_train, y_trainhat, y_test, y_testhat, title=""):
    matplotlib.rcParams.update({"font.size": 22})
    assert len(y_train) == len(y_trainhat)
    assert len(y_test) == len(y_testhat)
    N_train, N_test = len(y_train), len(y_test)
    N = N_train + N_test
    x = np.array([h for h in range(0, N)])
    x_train, x_test = x[:N_train], x[N_train:]
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.plot(list(x_train)+[x_test[0]], list(y_train)+[y_test[0]], "g-o", linewidth=3, label="y_train")
    ax.plot(list(x_train)+[x_test[0]], list(y_trainhat)+[y_testhat[0]], "b--o", linewidth=2, label="y_trainhat")
    ax.plot(x_test, y_test, "g-o", linewidth=3, label="y_test")
    ax.plot(x_test, y_testhat, "b--o", linewidth=2, label="y_testhat")
    ax.plot([N_train-0.5, N_train-0.5], ax.get_ylim(), "r--",label="train/test")
    ax.legend(loc="lower right")
    plt.ylabel("y")
    plt.xlabel("time")
    fig.set_size_inches(WIDTH, HEIGHT)
    plt.show()

def scatter_pred_vs_actual(y, yhat, title=""):
    matplotlib.rcParams.update({"font.size": 22})
    assert len(y) == len(yhat)
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.plot(y, yhat, "bo", markersize=15.0, label="Actual")
    ax.plot(ax.get_xlim(), ax.get_ylim(), "g--", label="Ideal")
    ax.legend(loc="lower right")
    plt.ylabel("yhat")
    plt.xlabel("y")
    fig.set_size_inches(WIDTH, HEIGHT)
    plt.show()

def plot_any_vs_time(y, ylabel):
    matplotlib.rcParams.update({"font.size": 22})
    N = len(y)
    x = [h for h in range(0, N)]
    fig, ax = plt.subplots()
    ax.set_title(ylabel + " vs time")
    ax.plot(x, y, "g-")
    plt.ylabel(ylabel)
    plt.xlabel("time")
    fig.set_size_inches(WIDTH, HEIGHT)
    plt.show()


