import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


def train_predict(X, y, first, last, model, target_variable):
    y = y.interpolate().bfill()
    X = pd.DataFrame(StandardScaler().fit_transform(X), columns=X.columns)

    predictions = pd.DataFrame(index=range(first + 20, last), columns=[target_variable])
    year_range = range(first + 20 - 1, last)  # Need a minimal window size of 20

    for year in year_range:
        begin_training_window = first
        end_training_window = year

        y_train = y.loc[begin_training_window:end_training_window, target_variable]
        X_train = X.loc[begin_training_window - first : end_training_window - first, :]
        model.fit(X_train.values, y_train.values)
        X_test = X.loc[
            end_training_window - first + 1 : end_training_window - first + 1, :
        ]
        predictions.loc[end_training_window + 1] = model.predict(X_test.values)[0]

    return predictions


def test_model(
    vineyards,
    model,
    model_name,
    df_features,
    target_variable,
    predictors,
    first_vintage,
    last_vintage,
    plot=False,
):
    df_features = df_features.loc[:, (vineyards,)].copy()
    features = df_features.columns.get_level_values(1).unique()

    arrays = [[model_name] * len(vineyards), vineyards]
    multi_index = pd.MultiIndex.from_arrays(arrays, names=("Model", "Vineyard"))
    df_predictions = pd.DataFrame(
        index=multi_index, columns=range(first_vintage + 20, last_vintage + 1)
    )
    for vineyard in vineyards:
        print(vineyard)
        df_features_extract = (
            df_features.loc[first_vintage:last_vintage, (vineyard, features)]
            .T.droplevel(0)
            .T.copy()
        )
        X = df_features_extract.drop(target_variable, axis=1)[predictors]
        y = df_features_extract[[target_variable]]
        predictions = train_predict(
            X, y, first_vintage, last_vintage, model, target_variable
        )

        if plot:
            plt.plot(predictions)
            plt.plot(y, color="green")
            plt.suptitle(target_variable)
            plt.show()
        df_predictions.loc[model_name, vineyard] = predictions.values.reshape(1, -1)

    return df_predictions
