import pandas as pd
import numpy as np
import datetime


def add_base_features(df_weather):
    df = df_weather.copy()
    df = df.drop(["Pl", "Ps", "Peff", "SoilHum", "Evap"], axis=1, errors="ignore")

    df["Frost"] = (df["Tn"] < 0).astype(int) * (-df["Tn"])
    df["DTR"] = df["Tx"] - df["Tn"]
    df["GDD10"] = ((df["Tx"] + df["Tn"]) / 2 > 10).astype(int) * (
        (df["Tx"] + df["Tn"]) / 2 - 10
    )

    df = df[["Tn", "Tm", "Tx", "DTR", "ETP", "P", "Frost", "GDD10"]]
    return df


def create_df(df_weather, df_pheno):
    original_features = list(df_weather.columns)
    vintages = list(df_pheno.loc[1960:].index)

    df = pd.DataFrame(index=vintages)

    intervals = {
        "budburst - flowering": ["Budburst", "Beginning flowering"],
        "flowering": ["Beginning flowering", "End flowering"],
        "flowering - véraison": ["End flowering", "Half véraison"],
        "véraison - harvest": ["Half véraison", "Beginning harvest"],
        "harvest": ["Beginning harvest", "End harvest"],
    }

    # Adding all base features, declined on all intervals
    for feature in original_features:
        subfeatures_list = [feature + ": " + interval for interval in intervals.keys()]

        for subfeature in subfeatures_list:
            df[subfeature] = 0

        for interval in intervals.keys():
            feature_name = feature + ": " + interval
            for vintage in vintages:
                date_begin = df_pheno.loc[vintage, intervals[interval][0]]
                date_end = df_pheno.loc[vintage, intervals[interval][1]]
                assert date_begin < date_end, "Error: date begin after date end!"
                if feature in ["Hail", "P", "Wind", "ETP", "GDD10", "Heavy Rain"]:
                    df.loc[vintage, feature_name] = df_weather.loc[
                        date_begin:date_end, feature
                    ].sum()

                # elif feature == 'GDD':
                #    date_debourrement = df_pheno.loc[vintage, 'debourrement']
                #    df.loc[vintage, feature_name] = df_weather.loc[date_debourrement:date_end, feature].sum()
                else:
                    df.loc[vintage, feature_name] = df_weather.loc[
                        date_begin:date_end, feature
                    ].mean()
    df["Growing Season Tm"] = np.nan
    for vintage in vintages:
        date_begin = datetime.date(vintage, 4, 1)  # Begin on April 1
        date_end = datetime.date(vintage, 9, 30)  # End in September

        df.loc[vintage, "Growing Season Tm"] = df_weather.loc[
            date_begin:date_end, "Tm"
        ].mean()

    df["Sq Growing Season Tm"] = df["Growing Season Tm"] ** 2

    for vintage in vintages:
        date_begin = datetime.date(vintage, 8, 1)
        date_end = datetime.date(vintage, 8, 30)
        df.loc[vintage, "August Rain"] = df_weather.loc[date_begin:date_end, "P"].mean()

    for vintage in vintages:
        date_begin = df_pheno.loc[vintage, "Budburst"]
        date_end = df_pheno.loc[vintage, "End harvest"]

        df.loc[vintage, "Total Rain"] = df_weather.loc[date_begin:date_end, "P"].mean()

    df["Winter Rain"] = 0
    for vintage in vintages[1:]:  # do not include first vintage
        date_begin = datetime.date(
            vintage - 1, 10, 1
        )  # Begin on October 1, previous year
        date_end = datetime.date(vintage, 3, 1)  # End mid March
        df.loc[vintage, "Winter Rain"] += df_weather.loc[
            date_begin:date_end, "P"
        ].mean()

    df["Flowering date"] = df_pheno["Beginning flowering"].dt.dayofyear

    df["GDD10"] = 0
    for vintage in vintages:  # do not include first vintage
        date_begin = datetime.date(vintage, 4, 1)
        date_end = df_pheno.loc[vintage, "End harvest"]
        df.loc[vintage, "GDD10"] += (df_weather.loc[date_begin:date_end, "GDD10"]).sum()

    df = df.drop(
        [
            "Frost: flowering - véraison",
            "Frost: véraison - harvest",
            "Frost: harvest",
            "Frost: flowering",
        ],
        axis=1,
    )

    etp_mean = np.mean(
        (df["ETP: flowering - véraison"] + df["ETP: véraison - harvest"])
    )
    p_mean = np.mean((df["P: flowering - véraison"] + df["P: véraison - harvest"]))
    print(p_mean / etp_mean)
    df["WD: flowering - harvest"] = (
        df["ETP: flowering - véraison"] + df["ETP: véraison - harvest"]
    ) / etp_mean - (
        df["P: flowering - véraison"] + df["P: véraison - harvest"]
    ) / p_mean

    return df


def load_prices(df):
    df_prices = df.copy()
    df_prices = df_prices.interpolate()
    df_prices.loc[
        (df_prices["Chateau"] == "Château Latour") & (df_prices["Vintage"] > 2012),
        "Price",
    ] = np.nan

    # NaNs are always ignored in Pandas aggregation functions
    df_prices = df_prices[["Vintage", "Chateau", "Price"]]
    df_prices = df_prices.pivot(index="Vintage", columns=["Chateau"])
    df_prices.columns = df_prices.columns.get_level_values(1)
    df_prices["Average price"] = df_prices.mean(axis=1)
    return df_prices
