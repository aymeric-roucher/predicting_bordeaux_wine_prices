import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.ticker as mticker
from PIL import Image
import seaborn as sns
from sklearn.preprocessing import StandardScaler


def standard_scale(X):
    return pd.DataFrame(
        StandardScaler().fit_transform(X), index=X.index, columns=X.columns
    )


def score_predictions(predictions, y, begin, end):
    spearman_r = round(spearmanr(y.loc[begin:end], predictions.loc[begin:end])[0], 3)
    mae = round(
        np.mean(np.abs(predictions.loc[begin:end].values - y.loc[begin:end].values)), 3
    )
    r2 = round(r2_score(y.loc[begin:end].values, predictions.loc[begin:end].values), 3)
    return np.array([spearman_r, r2, mae])


def score_models(df_predictions, df_true, begin, end, power_transformer=None):
    df_predictions = df_predictions.T
    models = list(df_predictions.columns.unique(level=0))
    vineyards_predictions = list(df_predictions.columns.unique(level=1))
    vineyards_true = list(df_true.columns.unique())
    vineyards = [
        vineyard for vineyard in vineyards_predictions if vineyard in vineyards_true
    ]

    score_index = pd.MultiIndex.from_arrays(
        [
            vineyards * 3,
            ["Spearman"] * len(vineyards)
            + ["R2"] * len(vineyards)
            + ["MAE"] * len(vineyards),
        ],
        names=("Vineyard", "Test variable"),
    )
    df_results = pd.DataFrame(index=score_index, columns=models)
    df_predictions.index = df_predictions.index.astype(int)
    for model in models:
        for vineyard in vineyards:
            time_range = range(begin, end + 1)
            if power_transformer is not None:
                true = pd.DataFrame(
                    power_transformer.inverse_transform(
                        df_true.loc[time_range, vineyard].values.reshape(-1, 1)
                    ),
                    index=time_range,
                )
                predictions = pd.DataFrame(
                    power_transformer.inverse_transform(
                        df_predictions.loc[
                            time_range, (model, vineyard)
                        ].values.reshape(-1, 1)
                    ),
                    index=time_range,
                )
            else:
                true = df_true.loc[time_range, vineyard]
                predictions = df_predictions.loc[time_range, (model, vineyard)]
            concat = pd.concat([predictions, true], axis=1).dropna(axis=0, how="any")

            df_results.loc[vineyard, model] = score_predictions(
                concat.iloc[:, 0], concat.iloc[:, 1], begin, end
            )
    return df_results.groupby(level=[1, 0]).sum()


def plot_predictions(df_predictions, df_true, begin, end, model, set_limits=True):
    df_predictions = df_predictions.T
    vineyards_predictions = list(df_predictions.columns.unique(level=1))
    vineyards_true = list(df_true.columns.unique())
    vineyards = [
        vineyard for vineyard in vineyards_predictions if vineyard in vineyards_true
    ]
    for vineyard in vineyards:
        print(vineyard)
        time_range = range(begin, end + 1)
        predictions = df_predictions.loc[time_range, (model, vineyard)]
        true = df_true.loc[time_range, vineyard]
        concat = pd.concat([predictions, true], axis=1)
        concat = concat.apply(pd.to_numeric)
        concat = np.exp(concat)
        concat.columns = ["Prediction", "True"]

        plt.figure(figsize=(7, 3))
        plt.grid(True, which="both", axis="both")
        sns.lineplot(
            data=concat,
            markers=["o"] * 2,
            dashes=[""] * 2,
            markersize=8,
            palette=["orange", "green"],
        )
        if set_limits:
            plt.gca().set_yticks([100, 200, 300])
            plt.ylim((70, 320))
        plt.ylabel("2021 price (€)")
        plt.xlabel("Vintage")

        plt.yscale("log")
        # plt.gca().yaxis.set_ticks([100,200])
        plt.gca().xaxis.set_ticks(time_range, minor=True)
        plt.gca().xaxis.set_ticks(range(begin, end + 1, 5), minor=False)

        plt.gca().yaxis.set_major_formatter(mticker.ScalarFormatter())
        plt.gca().yaxis.set_minor_formatter(mticker.NullFormatter())

        save_fig(
            f"views/model_outputs/lineplot_{model}_{vineyard}", width_column="single"
        )

        plt.show()
        plt.figure(figsize=(7, 3))
        sns.lineplot(
            data=concat.rank(ascending=False),
            markers=["o"] * 2,
            dashes=[""] * 2,
            markersize=8,
            palette=["orange", "green"],
        )
        plt.grid(True, which="both", axis="both")
        plt.ylabel("2021 rank")
        plt.xlabel("Vintage")
        plt.ylim((0, len(concat) + 1))
        plt.yticks(range(1, len(concat) + 1, 5))
        plt.gca().invert_yaxis()
        plt.gca().xaxis.set_ticks(time_range, minor=True)
        plt.gca().xaxis.set_ticks(range(begin, end + 1, 5), minor=False)
        save_fig(f"views/model_outputs/rank_{model}_{vineyard}", width_column="single")
        plt.show()

        plt.figure(figsize=(5, 4))
        if set_limits:
            plt.yscale("log")
            plt.xscale("log")
        viridis = cm.get_cmap("viridis", 8)
        plt.grid(True, which="both", axis="both")
        if set_limits:
            plt.plot(range(70, 320), range(70, 320), color="k", zorder=-3)
        concat["Vintage"] = pd.to_numeric(concat.index)
        ax = sns.scatterplot(
            data=concat, x="True", y="Prediction", hue="Vintage", palette=viridis
        )
        plt.ylabel("Model prediction (€)")
        plt.xlabel("2021 price(€)")
        if set_limits:
            plt.ylim((70, 320))
            plt.xlim((70, 320))
        norm = plt.Normalize(concat["Vintage"].min(), concat["Vintage"].max())
        sm = plt.cm.ScalarMappable(cmap=viridis, norm=norm)
        sm.set_array([])
        ax.get_legend().remove()
        ax.figure.colorbar(sm)
        if set_limits:
            plt.gca().set_yticks([100, 200])
            plt.gca().set_xticks([100, 200])

        save_fig(f"views/model_outputs/fit_{model}_{vineyard}", width_column="single")

        plt.show()
    return


def process_ratings(df_ratings):
    df_ratings = df_ratings.copy()
    df_ratings["Rating"] = (df_ratings["Rating - LB"] + df_ratings["Rating - HB"]) / 2
    df_ratings = df_ratings[df_ratings["Vintage"] < 2018]
    df_ratings["Vintage"] = df_ratings["Vintage"].astype(np.int32)
    df_ratings = df_ratings[["Chateau", "Vintage", "Rating"]]
    df_ratings = df_ratings.pivot(index="Chateau", columns="Vintage")
    df_ratings.columns = range(1994, 2018)
    for vintage in range(1994, 2018):
        df_ratings.loc["Average", vintage] = np.array(
            round(df_ratings[vintage].mean(), 1)
        ).astype(np.float64)
    df_ratings.index = df_ratings.index.get_level_values(0)
    df_ratings["Model"] = "Rating"
    df_ratings.set_index("Model", append=True, inplace=True)
    df_ratings.index = df_ratings.index.swaplevel()
    return df_ratings


def save_fig(path, width_column):
    assert width_column in ["single", "1.5", "double"]
    current_width = plt.gcf().get_size_inches()[0]
    point_size = {
        "single": 3543,
        "1.5": 5512,
        "double": 7480,
    }
    plt.savefig(
        path + ".png",
        bbox_inches="tight",
        dpi=int(point_size[width_column] / current_width) + 1,
    )
    image = Image.open(path + ".png")
    non_transparent = Image.new("RGBA", image.size, (255, 255, 255, 255))
    non_transparent.paste(image, (0, 0), image)
    non_transparent.convert("RGB").save(path + ".jpg")
    return
