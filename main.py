#!/usr/bin/env python3

# Imports
from src.extract import parse_xml
from src.analysis import *
from src.export import export_year_sheet
from src.clean import clean_xml_file
import argparse

# Add and Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--xml", required=True)
parser.add_argument("--organization", required=True)
parser.add_argument("--year", required=True)

args = parser.parse_args()

# Global declarations
FILENAME = args.xml
ORGANIZATION = args.organization if len(args.organization) > 0 else args.xml.split('/')[-1].split('_')[0]
YEAR = args.year if len(args.year) > 0 else args.xml.split('/')[-1].split('_')[1][:-4]
SHEETNAME = f'{ORGANIZATION}_{YEAR}.xlsx'

# Extract data
clean_xml_file(FILENAME)
data = parse_xml(FILENAME)

# Create tables
tables = []
tables_to_print = ['all']

if 'master' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Master Grants Table',
        'data' : get_master(data)
    }) # Add Master Grants Table

if 'stats' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Grants Statistics Table',
        'data' : get_min_max_median_table(data)
    }) # Add min/max Table

if 'unique' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Unique Amounts Table',
        'data' : get_unique_amounts_table(data)
    }) # Add Unique Amounts Table

if 'range' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Grants Distributed by Range Table',
        'data' : get_grants_by_range(data)
    }) # Add Grants Distributed by Range Table

if 'location' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Grants Distributed by Location Table',
        'data' : get_location_distribution_table(data)
    }) # Add Grants Distributed by Location Table

if 'category' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'Grants Distributed by Categories Table',
        'data' : get_category_distribution_table(data)
    }) # Add Grants Distributed by Categories Table

if 'states' in tables_to_print or 'all' in tables_to_print:
    tables.append({
        'title' : 'States and Counties Table',
        'data' : get_state_cities_table(data)
    }) # Add States and Counties Table

# Export the tables
with pd.ExcelWriter(f'output/{SHEETNAME}', engine="openpyxl") as writer:
    export_year_sheet(writer, YEAR, tables)

print(f"[+] Successfully created output/{SHEETNAME}.")
