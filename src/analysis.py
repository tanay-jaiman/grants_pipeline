#!/usr/bin/env python3

# Imports
import pandas as pd

from src.config import (
    MASTER_TABLE_CONFIG,
    STATS_TABLE_CONFIG,
    UNIQUE_AMOUNTS_TABLE_CONFIG,
    RANGE_TABLE_CONFIG,
    LOCATION_TABLE_CONFIG,
    CATEGORY_TABLE_CONFIG,
    CITIES_STATE_CONFIG
)


# 1. Create master table
def get_master(df: pd.DataFrame):

    temp_df = df.copy()

    temp_df['location'] = (
        temp_df['address'].fillna('') + ' ' +
        temp_df['city'].fillna('') + ', ' +
        temp_df['state'].fillna('') + ' ' +
        temp_df['zip'].fillna('')
    )

    master_df = temp_df[
        list(MASTER_TABLE_CONFIG['columns'].keys())
    ]

    master_df = master_df.rename(
        columns=MASTER_TABLE_CONFIG['columns']
    )

    total_row = pd.DataFrame([{
        "Recipient Name": "TOTAL",
        "Amount": master_df["Amount"].sum()
    }])

    master_df = pd.concat(
        [master_df, total_row],
        ignore_index=True
    )

    return master_df


# 2. Create min/max/median table
def get_min_max_median_table(df: pd.DataFrame):

    stats_df = pd.DataFrame({
        "Metric": ["Minimum", "Maximum", "Median"],
        "Value": [
            df["amount"].min(),
            df["amount"].max(),
            df["amount"].median()
        ]
    })

    stats_df = stats_df.rename(
        columns=STATS_TABLE_CONFIG["columns"]
    )

    return stats_df


# 3. Create unique amounts table
def get_unique_amounts_table(df: pd.DataFrame):

    unique_df = (
        df['amount']
        .value_counts()
        .reset_index()
    )

    unique_df.columns = list(
        UNIQUE_AMOUNTS_TABLE_CONFIG["columns"].keys()
    )

    unique_df = unique_df.rename(
        columns=UNIQUE_AMOUNTS_TABLE_CONFIG["columns"]
    )

    unique_df = unique_df.sort_values(
        by='Amount',
        ascending=True
    )

    total_row = pd.DataFrame([{
        "Amount": "TOTAL",
        "No. of Grants": unique_df["No. of Grants"].sum()
    }])

    unique_df = pd.concat(
        [unique_df, total_row],
        ignore_index=True
    )

    return unique_df


# 4. Create Grants by range and recipients table
def get_grants_by_range(
    df: pd.DataFrame,
    step: int = 10000,
    remove_empty: bool = False
):

    min_amount = int(df["amount"].min())
    max_amount = int(df["amount"].max())

    start = (min_amount // step) * step
    end = ((max_amount // step) + 1) * step

    bins = list(range(start, end + step, step))

    labels = []

    for i in range(len(bins) - 1):

        lower = bins[i]
        upper = bins[i + 1]

        labels.append(
            f"${lower:,} - ${upper:,}"
        )

    temp_df = df.copy()

    temp_df["grant_range"] = pd.cut(
        temp_df["amount"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    range_df = (
        temp_df
        .groupby("grant_range")
        .agg(
            number_of_grants=("amount", "count"),

            unique_amounts=("amount", lambda x:
                ", ".join(
                    map(
                        lambda n: f"{int(n):,}",
                        sorted(x.unique())
                    )
                )
            ),

            total_amount=("amount", "sum"),

            recipients=("state", lambda x:
                ", ".join(sorted(x.unique()))
            )
        )
        .reset_index()
    )

    if remove_empty:
        range_df = range_df[
            range_df["number_of_grants"] > 0
        ]

    range_df.columns = list(
        RANGE_TABLE_CONFIG["columns"].keys()
    )

    range_df = range_df.rename(
        columns=RANGE_TABLE_CONFIG["columns"]
    )

    return range_df


# 5. Create Location distribution table
def get_location_distribution_table(df: pd.DataFrame):

    temp_df = df.copy()

    total_grants = len(temp_df)
    total_amount = temp_df["amount"].sum()

    location_df = (
        temp_df
        .groupby("state")
        .agg(
            number_of_grants=("amount", "count"),

            total_grant_amount=("amount", "sum")
        )
        .reset_index()
    )

    location_df["percentage_by_number"] = (
        location_df["number_of_grants"]
        / total_grants
        * 100
    ).round(2)

    location_df["percentage_by_amount"] = (
        location_df["total_grant_amount"]
        / total_amount
        * 100
    ).round(2)

    location_df.columns = list(
        LOCATION_TABLE_CONFIG["columns"].keys()
    )

    location_df = location_df.rename(
        columns=LOCATION_TABLE_CONFIG["columns"]
    )

    total_row = pd.DataFrame([{
        "Location": "TOTAL",
        "No. of Grants": location_df["No. of Grants"].sum(),
        "Percentage by Number (%)": 100.00,
        "Amount of Total Grants Distributed":
            location_df["Amount of Total Grants Distributed"].sum(),
        "Percentage by Amount Distributed (%)": 100.00
    }])

    location_df = pd.concat(
        [location_df, total_row],
        ignore_index=True
    )

    return location_df

# 6. Create grant distribution by category table
def get_category_distribution_table(df: pd.DataFrame):

    temp_df = df.copy()

    total_grants = len(temp_df)
    total_amount = temp_df["amount"].sum()

    category_df = (
        temp_df
        .groupby("category")
        .agg(
            total_amount=("amount", "sum"),

            number_of_grants=("amount", "count")
        )
        .reset_index()
    )

    category_df["percentage_by_number"] = (
        category_df["number_of_grants"]
        / total_grants
        * 100
    ).round(2)

    category_df["percentage_by_amount"] = (
        category_df["total_amount"]
        / total_amount
        * 100
    ).round(2)

    category_df = category_df.sort_values(
        by="total_amount",
        ascending=False
    )

    category_df = category_df.rename(
        columns=CATEGORY_TABLE_CONFIG["columns"]
    )

    total_row = pd.DataFrame([{
        "Category": "TOTAL",

        "Total Amount":
            category_df["Total Amount"].sum(),

        "No. of Grants":
            category_df["No. of Grants"].sum(),

        "Percentage by Number (%)": 100.00,

        "Percentage by Amount Distributed (%)": 100.00
    }])

    category_df = pd.concat(
        [category_df, total_row],
        ignore_index=True
    )

    return category_df

# 7. Create state and city table
def get_state_cities_table(df: pd.DataFrame):
    temp_df = df.copy()

    temp_df = temp_df.dropna(
        subset=["state", "city"]
    )

    temp_df["state"] = temp_df["state"].str.strip().str.upper()
    temp_df["city"] = temp_df["city"].str.strip().str.lower().str.title()

    cities_df = (
        temp_df
        .groupby("state")
        .agg(
            counties=("city", lambda x:
                ", ".join(
                    sorted(
                        x.dropna().unique()
                    )
                )
            )
        )
        .reset_index()
    )

    cities_df.columns = list(
        CITIES_STATE_CONFIG["columns"].keys()
    )

    cities_df = cities_df.rename(
        columns=CITIES_STATE_CONFIG["columns"]
    )

    cities_df = cities_df.sort_values(
        by="State"
    )

    return cities_df
