#!/usr/bin/env python3

# Imports
import pandas as pd

from src.config import (
    RANGE_STEP_OVERRIDE,
    RANGE_TARGET_BUCKETS,
    RANGE_MIN_BUCKETS,
    RANGE_MAX_BUCKETS,
    RANGE_MIN_NICE_BOUNDARY,
    MASTER_TABLE_CONFIG,
    STATS_TABLE_CONFIG,
    UNIQUE_AMOUNTS_TABLE_CONFIG,
    RANGE_TABLE_CONFIG,
    LOCATION_TABLE_CONFIG,
    CATEGORY_TABLE_CONFIG,
    CITIES_STATE_CONFIG
)
from src.distance import add_distance_labels


NICE_STEP_MULTIPLIERS = (1, 2, 2.5, 5, 10)
NICE_BOUNDARY_MULTIPLIERS = (1, 2, 5)


def _format_range_amount(amount: float) -> str:
    return f"${int(amount):,}"


def _nice_step(raw_step: float) -> int:
    if raw_step <= 0:
        return 1

    magnitude = 1
    while magnitude * 10 < raw_step:
        magnitude *= 10

    for multiplier in NICE_STEP_MULTIPLIERS:
        step = int(multiplier * magnitude)

        if step >= raw_step:
            return max(step, 1)

    return magnitude * 10


def _nice_money_boundaries(max_amount: int) -> list[int]:
    boundaries = [0, RANGE_MIN_NICE_BOUNDARY]
    magnitude = RANGE_MIN_NICE_BOUNDARY

    while magnitude <= max_amount * 10:
        for multiplier in NICE_BOUNDARY_MULTIPLIERS:
            boundary = multiplier * magnitude

            if boundary > boundaries[-1]:
                boundaries.append(boundary)

            if boundary > max_amount:
                return boundaries

        magnitude *= 10

    return boundaries


def _build_amount_bins(amounts: pd.Series, step_override: int | None = None):
    min_amount = int(amounts.min())
    max_amount = int(amounts.max())
    positive_amounts = amounts[amounts > 0]
    positive_min = int(positive_amounts.min()) if not positive_amounts.empty else 0

    if min_amount == max_amount:
        lower = max(0, min_amount - 1)
        upper = max_amount + 1
        return [lower, upper], [f"{_format_range_amount(min_amount)}"]

    if step_override:
        step = int(step_override)
    elif RANGE_STEP_OVERRIDE:
        step = int(RANGE_STEP_OVERRIDE)
    elif positive_min > 0 and max_amount / positive_min > RANGE_TARGET_BUCKETS:
        bins = _nice_money_boundaries(max_amount)

        labels = []

        for index in range(len(bins) - 1):
            lower = bins[index]
            upper = bins[index + 1]

            labels.append(
                f"{_format_range_amount(lower)} - {_format_range_amount(upper - 1)}"
            )

        return bins, labels
    else:
        spread = max_amount - min_amount
        step = _nice_step(spread / RANGE_TARGET_BUCKETS)

    if step <= 0:
        raise ValueError("Range step must be greater than zero.")

    start = (min_amount // step) * step
    end = ((max_amount // step) + 1) * step

    bins = list(range(start, end + step, step))

    while len(bins) - 1 > RANGE_MAX_BUCKETS:
        step = _nice_step(step * 1.5)
        start = (min_amount // step) * step
        end = ((max_amount // step) + 1) * step
        bins = list(range(start, end + step, step))

    while len(bins) - 1 < RANGE_MIN_BUCKETS and step > 1:
        candidate_step = _nice_step(step / 2)

        if candidate_step >= step:
            break

        candidate_start = (min_amount // candidate_step) * candidate_step
        candidate_end = ((max_amount // candidate_step) + 1) * candidate_step
        candidate_bins = list(range(
            candidate_start,
            candidate_end + candidate_step,
            candidate_step
        ))

        if len(candidate_bins) - 1 > RANGE_MAX_BUCKETS:
            break

        step = candidate_step
        bins = candidate_bins

    labels = []

    for index in range(len(bins) - 1):
        lower = bins[index]
        upper = bins[index + 1]

        labels.append(
            f"{_format_range_amount(lower)} - {_format_range_amount(upper - 1)}"
        )

    return bins, labels


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
    step: int | None = None,
    remove_empty: bool = True
):

    bins, labels = _build_amount_bins(df["amount"], step)

    temp_df = df.copy()

    temp_df["grant_range"] = pd.cut(
        temp_df["amount"],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=False
    )

    range_df = (
        temp_df
        .groupby("grant_range")
        .agg(
            number_of_grants=("amount", "count"),

            unique_amounts=("amount", lambda x:
                ", ".join(
                    map(
                        lambda n: str(int(n)),
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

    location_df = location_df.sort_values(
        by=[
            "Percentage by Amount Distributed (%)",
            "Amount of Total Grants Distributed",
            "Location"
        ],
        ascending=[False, False, True]
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
    temp_df = temp_df.sort_values(["state", "city"])

    def format_cities(state: str, group: pd.DataFrame) -> str:
        cities = sorted(group["city"].dropna().unique())
        cities = add_distance_labels(state, cities)
        return ", ".join(cities)

    city_labels = {
        state: format_cities(state, group)
        for state, group in temp_df.groupby("state")
    }

    cities_df = (
        temp_df
        .groupby("state")
        .agg(
            number_of_grants=("amount", "count"),
            total_amount=("amount", "sum")
        )
        .reset_index()
    )

    cities_df["counties"] = cities_df["state"].map(city_labels)
    cities_df = cities_df[
        ["state", "counties", "number_of_grants", "total_amount"]
    ]

    cities_df.columns = list(
        CITIES_STATE_CONFIG["columns"].keys()
    )

    cities_df = cities_df.rename(
        columns=CITIES_STATE_CONFIG["columns"]
    )

    cities_df = cities_df.sort_values(
        by=["No. of Grants", "Total Amount", "State"],
        ascending=[False, False, True]
    )

    total_row = pd.DataFrame([{
        "State": "TOTAL",
        "Counties": "",
        "No. of Grants": cities_df["No. of Grants"].sum(),
        "Total Amount": cities_df["Total Amount"].sum()
    }])

    cities_df = pd.concat(
        [cities_df, total_row],
        ignore_index=True
    )

    return cities_df
