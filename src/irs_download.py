#!/usr/bin/env python3

import argparse
import csv
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path


IRS_XML_BASE_URL = "https://apps.irs.gov/pub/epostcard/990/xml"


def download_irs_filings(
    ein: str,
    organization: str,
    index_year: str,
    tax_year: str = "",
    return_type: str = "990PF"
):
    matches = _find_index_matches(ein, index_year, tax_year, return_type)

    if not matches:
        raise ValueError("No matching IRS filings found.")

    output_dir = Path("input") / _safe_name(organization)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for match in matches:
            xml_path = _download_match(match, output_dir, temp_path)
            downloaded_files.append(xml_path)

    return downloaded_files


def _find_index_matches(ein, index_year, tax_year, return_type):
    normalized_ein = re.sub(r"\D", "", ein)
    index_url = f"{IRS_XML_BASE_URL}/{index_year}/index_{index_year}.csv"

    with urllib.request.urlopen(index_url) as response:
        rows = csv.DictReader(line.decode("utf-8") for line in response)

        matches = [
            row
            for row in rows
            if row["EIN"] == normalized_ein
            and row["RETURN_TYPE"].upper() == return_type.upper()
            and (not tax_year or row["TAX_PERIOD"].startswith(tax_year))
        ]

    return sorted(
        matches,
        key=lambda row: (row["TAX_PERIOD"], row["SUB_DATE"], row["OBJECT_ID"])
    )


def _download_match(match, output_dir, temp_path):
    batch_id = match["XML_BATCH_ID"]
    object_id = match["OBJECT_ID"]
    tax_year = match["TAX_PERIOD"][:4]
    zip_path = temp_path / f"{batch_id}.zip"

    if not zip_path.exists():
        zip_url = f"{IRS_XML_BASE_URL}/{match['SUB_DATE']}/{batch_id}.zip"
        urllib.request.urlretrieve(zip_url, zip_path)

    with zipfile.ZipFile(zip_path) as archive:
        xml_name = _find_xml_name(archive, object_id)
        xml_bytes = archive.read(xml_name)

    output_path = output_dir / f"{output_dir.name}_{tax_year}.xml"
    output_path.write_bytes(xml_bytes)
    return output_path


def _find_xml_name(archive, object_id):
    expected_names = {
        f"{object_id}_public.xml",
        f"{object_id}.xml"
    }

    for name in archive.namelist():
        filename = Path(name).name

        if filename in expected_names or object_id in filename:
            return name

    raise ValueError(f"Could not find XML object {object_id} in IRS batch.")


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_").lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ein", required=True)
    parser.add_argument("--organization", required=True)
    parser.add_argument("--index-year", required=True)
    parser.add_argument("--tax-year", default="")
    parser.add_argument("--return-type", default="990PF")

    args = parser.parse_args()

    files = download_irs_filings(
        ein=args.ein,
        organization=args.organization,
        index_year=args.index_year,
        tax_year=args.tax_year,
        return_type=args.return_type
    )

    for file in files:
        print(file)


if __name__ == "__main__":
    main()
