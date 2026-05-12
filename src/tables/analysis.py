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
from src.services.distance import add_distance_labels


NICE_STEP_MULTIPLIERS = (1, 2, 2.5, 5, 10)
NICE_BOUNDARY_MULTIPLIERS = (1, 2, 5)


def _apply_column_config(dataframe: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = config["columns"]
    available_columns = [
        column
        for column in columns.keys()
        if column in dataframe.columns
    ]

    return dataframe[available_columns].rename(columns=columns)


def _configured_column(config: dict, column: str) -> str:
    return config["columns"].get(column, column)


def _add_total_row(
    dataframe: pd.DataFrame,
    label_column: str,
    totals: dict
) -> pd.DataFrame:
    if label_column not in dataframe.columns:
        return dataframe

    total_row = {label_column: "TOTAL"}

    for column, value in totals.items():
        if column in dataframe.columns:
            total_row[column] = value

    return pd.concat(
        [dataframe, pd.DataFrame([total_row])],
        ignore_index=True
    )


def _sort_by_existing_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
    ascending: list[bool]
) -> pd.DataFrame:
    sort_columns = []
    sort_ascending = []

    for column, direction in zip(columns, ascending):
        if column in dataframe.columns:
            sort_columns.append(column)
            sort_ascending.append(direction)

    if not sort_columns:
        return dataframe

    return dataframe.sort_values(
        by=sort_columns,
        ascending=sort_ascending
    )


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

    master_df = _apply_column_config(temp_df, MASTER_TABLE_CONFIG)
    label_column = _configured_column(MASTER_TABLE_CONFIG, "name")
    amount_column = _configured_column(MASTER_TABLE_CONFIG, "amount")

    master_df = _add_total_row(
        master_df,
        label_column,
        {
            amount_column: master_df[amount_column].sum()
            if amount_column in master_df.columns
            else None
        }
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

    stats_df = _apply_column_config(stats_df, STATS_TABLE_CONFIG)

    return stats_df


# 3. Create unique amounts table
def get_unique_amounts_table(df: pd.DataFrame):

    unique_df = (
        df['amount']
        .value_counts()
        .reset_index()
    )

    unique_df.columns = ["Amount", "Number of Grants"]

    unique_df = _apply_column_config(unique_df, UNIQUE_AMOUNTS_TABLE_CONFIG)
    amount_column = _configured_column(UNIQUE_AMOUNTS_TABLE_CONFIG, "Amount")
    count_column = _configured_column(
        UNIQUE_AMOUNTS_TABLE_CONFIG,
        "Number of Grants"
    )

    unique_df = _sort_by_existing_columns(
        unique_df,
        [amount_column],
        [True]
    )

    unique_df = _add_total_row(
        unique_df,
        amount_column,
        {
            count_column: unique_df[count_column].sum()
            if count_column in unique_df.columns
            else None
        }
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

    range_df = range_df.rename(
        columns={
            "grant_range": "Range",
            "number_of_grants": "No. of Grants",
            "unique_amounts": "Unique Amounts",
            "total_amount": "Total Amount",
            "recipients": "Recipients"
        }
    )

    range_df = _apply_column_config(range_df, RANGE_TABLE_CONFIG)

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

    location_df = location_df.rename(
        columns={
            "state": "Location",
            "number_of_grants": "No. of Grants",
            "total_grant_amount": "Amount of Total Grants Distributed",
            "percentage_by_number": "Percentage by Number (%)",
            "percentage_by_amount": "Percentage by Amount Distributed (%)"
        }
    )

    location_df = _apply_column_config(location_df, LOCATION_TABLE_CONFIG)
    location_column = _configured_column(LOCATION_TABLE_CONFIG, "Location")
    count_column = _configured_column(LOCATION_TABLE_CONFIG, "No. of Grants")
    amount_column = _configured_column(
        LOCATION_TABLE_CONFIG,
        "Amount of Total Grants Distributed"
    )
    percent_number_column = _configured_column(
        LOCATION_TABLE_CONFIG,
        "Percentage by Number (%)"
    )
    percent_amount_column = _configured_column(
        LOCATION_TABLE_CONFIG,
        "Percentage by Amount Distributed (%)"
    )

    location_df = _sort_by_existing_columns(
        location_df,
        [
            percent_amount_column,
            amount_column,
            location_column
        ],
        [False, False, True]
    )

    location_df = _add_total_row(
        location_df,
        location_column,
        {
            count_column: location_df[count_column].sum()
            if count_column in location_df.columns
            else None,
            percent_number_column: 100.00,
            amount_column:
                location_df[amount_column].sum()
                if amount_column in location_df.columns
                else None,
            percent_amount_column: 100.00
        }
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

    category_df = _apply_column_config(category_df, CATEGORY_TABLE_CONFIG)
    category_column = _configured_column(CATEGORY_TABLE_CONFIG, "category")
    amount_column = _configured_column(CATEGORY_TABLE_CONFIG, "total_amount")
    count_column = _configured_column(CATEGORY_TABLE_CONFIG, "number_of_grants")
    percent_number_column = _configured_column(
        CATEGORY_TABLE_CONFIG,
        "percentage_by_number"
    )
    percent_amount_column = _configured_column(
        CATEGORY_TABLE_CONFIG,
        "percentage_by_amount"
    )

    category_df = _add_total_row(
        category_df,
        category_column,
        {
            amount_column: category_df[amount_column].sum()
            if amount_column in category_df.columns
            else None,
            count_column: category_df[count_column].sum()
            if count_column in category_df.columns
            else None,
            percent_number_column: 100.00,
            percent_amount_column: 100.00
        }
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
    cities_df = cities_df.rename(
        columns={
            "state": "State",
            "counties": "Counties",
            "number_of_grants": "No. of Grants",
            "total_amount": "Total Amount"
        }
    )

    cities_df = _apply_column_config(cities_df, CITIES_STATE_CONFIG)
    state_column = _configured_column(CITIES_STATE_CONFIG, "State")
    counties_column = _configured_column(CITIES_STATE_CONFIG, "Counties")
    count_column = _configured_column(CITIES_STATE_CONFIG, "No. of Grants")
    amount_column = _configured_column(CITIES_STATE_CONFIG, "Total Amount")

    cities_df = _sort_by_existing_columns(
        cities_df,
        [count_column, amount_column, state_column],
        [False, False, True]
    )

    cities_df = _add_total_row(
        cities_df,
        state_column,
        {
            counties_column: "",
            count_column: cities_df[count_column].sum()
            if count_column in cities_df.columns
            else None,
            amount_column: cities_df[amount_column].sum()
            if amount_column in cities_df.columns
            else None
        }
    )

    return cities_df
