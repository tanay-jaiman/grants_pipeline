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
    "start_row": 4,
    "start_col": 7,

    "columns": {
        "Metric": "Metric",
        "Value": "Value"
    }
}

UNIQUE_AMOUNTS_TABLE_CONFIG = {
    "title": "Unique Amount Table",
    "start_row": 10,
    "start_col": 7,

    "columns": {
        "Amount": "Amount",
        "Number of Grants": "No. of Grants"
    }
}

RANGE_TABLE_CONFIG = {
    "title": "Grants By Range and Recipients",
    "start_row": 3,
    "start_col": 10,

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
    "start_row": 3,
    "start_col": 16,

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
    "start_row": 13,
    "start_col": 10,

    "columns": {
        "category": "Category",
        "total_amount": "Total Amount",
        "number_of_grants": "No. of Grants",
        "percentage_by_number": "Percentage by Number (%)",
        "percentage_by_amount": "Percentage by Amount Distributed (%)"
    }
}

CITIES_STATE_CONFIG = {
    "title": "Location - State and Counties",
    "start_row": 22,
    "start_col": 10,

    "columns": {
        "State": "State",
        "Counties": "Counties"
    }
}
