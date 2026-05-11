#!/bin/bash

set -e

# Move to project directory
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

choose_org_folder() {
    # Pick the organization first so batch runs can process every year together.
    find input -mindepth 1 -maxdepth 1 -type d | sort | fzf \
        --prompt="Organization folder > " \
        --height=40% \
        --border \
        --preview='find {} -maxdepth 1 -name "*.xml" | sort | sed "s#^.*/##"'
}

choose_run_mode() {
    printf "Single XML file\nAll XML files in folder\nDownload IRS XML by EIN\n" | fzf \
        --prompt="Run mode > " \
        --height=20% \
        --border
}

choose_xml_file() {
    local org_folder="$1"

    find "$org_folder" -maxdepth 1 -type f -name "*.xml" | sort | fzf \
        --prompt="XML file > " \
        --height=40% \
        --border \
        --preview='sed -n "1,40p" {}'
}

infer_year() {
    local xml_file="$1"
    local filename

    filename=$(basename "$xml_file")

    if [[ "$filename" =~ ([0-9]{4}) ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

run_pipeline() {
    local xml_file="$1"
    local organization="$2"
    local year="$3"

    echo ""
    echo "[+] Processing $xml_file"
    echo "    Organization: $organization"
    echo "    Year: $year"

    python3 main.py \
        --xml "$xml_file" \
        --organization "$organization" \
        --year "$year"
}

ORG_FOLDER=$(choose_org_folder || true)

if [ -z "$ORG_FOLDER" ]; then
    echo "No organization folder selected."
    exit 1
fi

DEFAULT_ORG=$(basename "$ORG_FOLDER")
read -p "Organization Name [$DEFAULT_ORG]: " ORG_NAME
ORG_NAME=${ORG_NAME:-$DEFAULT_ORG}

RUN_MODE=$(choose_run_mode || true)

if [ -z "$RUN_MODE" ]; then
    echo "No run mode selected."
    exit 1
fi

if [ "$RUN_MODE" = "Single XML file" ]; then
    XML_FILE=$(choose_xml_file "$ORG_FOLDER" || true)

    if [ -z "$XML_FILE" ]; then
        echo "No XML file selected."
        exit 1
    fi

    DEFAULT_YEAR=$(infer_year "$XML_FILE")
    read -p "Year [$DEFAULT_YEAR]: " YEAR
    YEAR=${YEAR:-$DEFAULT_YEAR}

    if [ -z "$YEAR" ]; then
        echo "Year is required."
        exit 1
    fi

    run_pipeline "$XML_FILE" "$ORG_NAME" "$YEAR"
elif [ "$RUN_MODE" = "All XML files in folder" ]; then
    XML_FILES=()

    while IFS= read -r xml_file; do
        XML_FILES+=("$xml_file")
    done < <(find "$ORG_FOLDER" -maxdepth 1 -type f -name "*.xml" | sort)

    if [ ${#XML_FILES[@]} -eq 0 ]; then
        echo "No XML files found in $ORG_FOLDER."
        exit 1
    fi

    echo ""
    echo "[+] Found ${#XML_FILES[@]} XML files in $ORG_FOLDER."

    for XML_FILE in "${XML_FILES[@]}"; do
        YEAR=$(infer_year "$XML_FILE")

        if [ -z "$YEAR" ]; then
            read -p "Year for $XML_FILE: " YEAR
        fi

        if [ -z "$YEAR" ]; then
            echo "Skipping $XML_FILE because no year was provided."
            continue
        fi

        run_pipeline "$XML_FILE" "$ORG_NAME" "$YEAR"
    done
else
    read -p "EIN: " EIN
    read -p "IRS index filing year [$(date +%Y)]: " INDEX_YEAR
    INDEX_YEAR=${INDEX_YEAR:-$(date +%Y)}
    read -p "Tax year to download [all matches]: " TAX_YEAR
    read -p "Return type [990PF]: " RETURN_TYPE
    RETURN_TYPE=${RETURN_TYPE:-990PF}

    echo ""
    echo "[+] Downloading IRS XML filings..."

    python3 -m src.irs_download \
        --ein "$EIN" \
        --organization "$ORG_NAME" \
        --index-year "$INDEX_YEAR" \
        --tax-year "$TAX_YEAR" \
        --return-type "$RETURN_TYPE"
fi
