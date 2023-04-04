import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from tqdm import tqdm


class LPM_LS:
    def __init__(self, kernel, degree=0):
        self.coef_ = None
        self.n = None
        self.L = None
        self.degree = degree
        self.kernel = kernel
        self.h = None

    def fit(self, X, y, h):
        X = X.to_numpy()
        self.n, self.L = X.shape

        # Add 1 columns to the left of X
        X = np.hstack([np.ones((self.n, 1)), X])
        self.distance_matrix = np.hstack(
            [np.arange(-self.n + 1, 1).reshape(-1, 1) for _ in range(self.L + 1)]
        )
        W = np.eye(self.n)
        for i in range(self.n):
            W[i, i] = self.kernel(self.n, self.n, i, h)

        X = np.hstack([X * self.distance_matrix ** i for i in range(self.degree + 1)])
        self.coef_ = np.linalg.inv(X.T @ W @ X) @ X.T @ W @ y

    def _get_bandwidth_MSE(self, h, X, y):
        error = 0
        for i in range(self.n):
            X_i = np.concatenate([X[:i, :], X[i + 1 :, :]], axis=0)
            distances_list = [i - j for j in range(self.n) if j != i]
            self.distance_matrix = np.hstack(
                [np.array(distances_list).reshape(-1, 1) for _ in range(self.L + 1)]
            )
            W = np.eye(self.n - 1)
            for j in range(self.n):
                if j < i:
                    W[j, j] = self.kernel(self.n, i, j, h)
                if j > i:
                    W[j - 1, j - 1] = self.kernel(self.n, i, j, h)

            X_i = np.hstack(
                [X_i * self.distance_matrix ** i for i in range(self.degree + 1)]
            )
            result = (
                np.linalg.inv(X_i.T @ W @ X_i)
                @ X_i.T
                @ W
                @ np.concatenate([y[:i], y[i + 1 :]], axis=0)
                @ X_i.T
            )
            error += np.square(result - y[i])
        return error

    def get_all_bandwidth_MSEs(self, X, y, range):
        X = X.to_numpy()
        self.n, self.L = X.shape

        # Add 1 columns to the left of X
        X = np.hstack([np.ones((self.n, 1)), X])

        losses = []
        for h in tqdm(range):
            losses.append(self._get_bandwidth_MSE(h, X, y))

        return pd.DataFrame(losses, index=range)

    def get_best_bandwidth(self, X, y):
        losses = self.get_all_bandwidth_MSEs(X, y.values, np.arange(0.1,1, 0.01))
        means = losses.median(axis=1)
        return means.idxmin(axis=0)

    def predict(self, X):
        X = np.hstack([np.hstack([np.ones((1, 1)), X]) for _ in range(self.degree + 1)])
        return self.coef_ @ X.T

    def get_next_vintage_coeffs(self):
        return sum(
            [
                self.coef_[self.L * i : (self.L * (i + 1)) + 1]
                for i in range(self.degree + 1)
            ]
        )

    def get_coeffs(self):
        coeffs = sum(
            [
                np.vstack(
                    [
                        (self.distance_matrix ** i)[:, j] * self.coef_[self.L * i + j]
                        for j in range(self.L + 1)
                    ]
                ).T
                for i in range(self.degree + 1)
            ]
        )
        return coeffs


def linear_train_predict(
    X: pd.DataFrame,
    y: pd.DataFrame,
    first: int,
    last: int,
    model: object,
    target_variable: str,
    plot: bool,
    vineyard: str,
    fixed_bandwidth: float = None,
):
    y = y.interpolate().bfill()
    X = pd.DataFrame(StandardScaler().fit_transform(X), columns=X.columns)

    predictions = pd.DataFrame(
        index=range(first + 20, last), columns=[target_variable]
    )
    year_range = range(first + 20 - 1, last) # Need a minimal window size of 20
    coeffs = pd.DataFrame(index=year_range, columns=["intercept"] + list(X.columns))

    for year in year_range:
        begin_training_window = first
        end_training_window = year - 3

        y_train = y.loc[begin_training_window:end_training_window, target_variable]
        X_train = X.loc[begin_training_window-first:end_training_window - first, :]
        if fixed_bandwidth is None:
            best_bandwidth = model.get_best_bandwidth(X_train, y_train)
            model.fit(X_train, y_train.values, best_bandwidth)
        else:
            model.fit(X_train, y_train.values, fixed_bandwidth)
        X_test = X.loc[year + 1 - first:year + 1 - first, :]
        predictions.loc[year + 1] = model.predict(X_test.values)[0]
        coeffs.loc[
            year, ["intercept"] + list(X.columns)
        ] = model.get_next_vintage_coeffs()

    return predictions, coeffs.apply(pd.to_numeric)


def linear_test_model(
    vineyards,
    model,
    model_name,
    df_features,
    target_variable,
    predictors,
    first_vintage,
    last_vintage,
    plot=False,
    fixed_bandwidth: float=None,
):
    df_features = df_features.loc[:, (vineyards,)].copy()
    features = df_features.columns.get_level_values(1).unique()

    arrays = [[model_name] * len(vineyards), vineyards]
    multi_index = pd.MultiIndex.from_arrays(arrays, names=("Model", "Vineyard"))
    df_predictions = pd.DataFrame(
        index=multi_index, columns=range(first_vintage + 20, last_vintage + 1)
    )
    coeffs = {}
    tbar = tqdm(vineyards)
    for vineyard in tbar:
        tbar.set_description(vineyard)
        df_features_extract = (
            df_features.loc[first_vintage:last_vintage, (vineyard, features)]
            .T.droplevel(0)
            .T.copy()
        )
        X = df_features_extract.drop(target_variable, axis=1)[predictors]
        y = df_features_extract[[target_variable]]
        predictions, coeffs[vineyard] = linear_train_predict(
            X,
            y,
            first_vintage,
            last_vintage,
            model,
            target_variable,
            plot,
            vineyard,
            fixed_bandwidth=fixed_bandwidth,
        )

        if plot:
            plt.plot(predictions)
            plt.plot(y, color="green")
            plt.suptitle(target_variable)
            plt.show()
        df_predictions.loc[model_name, vineyard] = predictions.values.reshape(1, -1)

    return df_predictions, coeffs
