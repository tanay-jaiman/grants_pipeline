#!/bin/bash

# Move to project directory
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Select XML file
XML_FILE=$(find input -name "*.xml" | fzf)

if [ -z "$XML_FILE" ]; then
    echo "No XML file selected."
    exit 1
fi

# Gather metadata
read -p "Organization Name: " ORG_NAME

read -p "Year: " YEAR

# Run pipeline
python3 main.py \
    --xml "$XML_FILE" \
    --organization "$ORG_NAME" \
    --year "$YEAR"