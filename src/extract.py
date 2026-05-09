#!/usr/bin/env python3

# Imports 
import pandas as pd
from lxml import etree
from src.grant_search import extract_grant_info, categorize_purpose

# Parse the xml file
def parse_xml(filepath: str):
    # Grab root
    tree = etree.parse(filepath)
    root = tree.getroot()

    # Global declarations
    grants = []
    ns = {"irs": "http://www.irs.gov/efile"}


    # Extract all relevant information (name, address, etc.) for each recipient
    for grant in root.findall(".//irs:GrantOrContributionPdDurYrGrp", namespaces=ns):

        # Search all relevant IRS XML Keywords
        grant_info = extract_grant_info(grant, ns)

        # store grant object in grants list
        grants.append(grant_info)

    # Load the date into a pandas DataFrame
    df = pd.DataFrame(grants)
    df['amount'] = pd.to_numeric(df['amount']) # Convert amount literals to numeric
    df = df.sort_values('amount', ascending=True).reset_index() # Sort according to grant amount ASCENDING

    df['purpose'] = [categorize_purpose(t) for t in df['name'] + ' ' + df['purpose']]

    # print(df.head())
    # print(df[['name', 'purpose', 'amount']].head())

    return df
