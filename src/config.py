#!/usr/bin/env python3

MASTER_TABLE_CONFIG = {
    "title": "Master Grants Table",
    "start_row": 0,
    "start_col": 0,

    "columns": {
        "name": "Recipient Name",
        "location": "Recipient Address",
        "relationship": "Relationship to Foundation Manager or Contributor",
        "status": "Recipient Foundation Status",
        "purpose": "Purpose of Grant or Contribution",
        "amount": "Amount"
    }
}

STATS_TABLE_CONFIG = {
    "title": "Grant Statistics",
    "start_row": 2,
    "start_col": 9,

    "columns": {
        "Metric": "Metric",
        "Value": "Value"
    }
}

UNIQUE_AMOUNTS_TABLE_CONFIG = {
    "title": "Unique Amount Table",
    "start_row": 8,
    "start_col": 9,

    "columns": {
        "Amount": "Amount",
        "Number of Grants": "No. of Grants"
    }
}

RANGE_TABLE_CONFIG = {
    "title": "Grants By Range and Recipients",
    "start_row": 2,
    "start_col": 13,

    "columns": {
        "Range": "Range",
        "No. of Grants": "No. of Grants",
        "Unique Amounts": "Unique Amounts",
        "Total Amount": "Total Amount",
        "Recipients": "Recipients"
    }
}

LOCATION_TABLE_CONFIG = {
    "title": "Location Distribution",
    "start_row": 25,
    "start_col": 15,

    "columns": {
        "Location": "Location",
        "No. of Grants": "No. of Grants",
        "Amount of Total Grants Distributed": "Amount of Total Grants Distributed",
        "Percentage by Number (%)": "Percentage by Number (%)",
        "Percentage by Amount Distributed (%)": "Percentage by Amount Distributed (%)"
    }
}

CATEGORY_TABLE_CONFIG = {
    "title": "Amount Distribution By Category",
    "spacing": 3,
    "start_col": 15,

    "columns": {
        "Category": "Category",
        "Total Amount": "Total Amount",
        "Approx. Percentage (%)": "Approx. Percentage (%)",
        "No. of Grants": "No. of Grants"
    }
}

CITIES_STATE_CONFIG = {
    "title": "State Counties Table",
    "start_row": 110,
    "start_col": 12,

    "columns": {
        "State": "State",
        "Counties": "Counties"
    }
}