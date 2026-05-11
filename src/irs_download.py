#!/usr/bin/env python3

import argparse
import csv
import re
import shutil
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
import urllib.request
import zipfile
from pathlib import Path


IRS_XML_BASE_URL = "https://apps.irs.gov/pub/epostcard/990/xml"


def download_irs_filings(
    ein: str,
    organization: str,
    index_years: str,
    tax_years: str = "",
    return_type: str = "990PF",
    skip_existing: bool = False
):
    matches = _find_index_matches(ein, index_years, tax_years, return_type)

    if not matches:
        raise ValueError("No matching IRS filings found.")

    output_dir = Path("input") / _safe_name(organization)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for match in matches:
            if skip_existing and _output_path_for_match(output_dir, match).exists():
                print(f"[=] Already have {match['TAX_PERIOD'][:4]}, skipping download.")
                continue

            try:
                xml_path = _download_match(match, output_dir, temp_path)
                downloaded_files.append(xml_path)
            except subprocess.CalledProcessError:
                print(
                    f"[!] Skipping {match['TAX_PERIOD']}: "
                    "IRS ZIP compression is not supported by local unzip tools."
                )
            except (
                HTTPError,
                NotImplementedError,
                URLError,
                ValueError
            ) as error:
                print(f"[!] Skipping {match['TAX_PERIOD']}: {error}")

    return downloaded_files


def _find_index_matches(ein, index_years, tax_years, return_type):
    normalized_ein = re.sub(r"\D", "", ein)
    index_year_list = _expand_years(index_years)
    tax_year_set = set(_expand_years(tax_years))
    matches_by_object_id = {}

    for index_year in index_year_list:
        index_url = f"{IRS_XML_BASE_URL}/{index_year}/index_{index_year}.csv"

        with urllib.request.urlopen(index_url) as response:
            rows = csv.DictReader(line.decode("utf-8") for line in response)

            for row in rows:
                row_tax_year = row["TAX_PERIOD"][:4]

                if row["EIN"] != normalized_ein:
                    continue

                if row["RETURN_TYPE"].upper() != return_type.upper():
                    continue

                if tax_year_set and row_tax_year not in tax_year_set:
                    continue

                matches_by_object_id[row["OBJECT_ID"]] = row

    return sorted(
        matches_by_object_id.values(),
        key=lambda row: (row["TAX_PERIOD"], row["SUB_DATE"], row["OBJECT_ID"])
    )


def _download_match(match, output_dir, temp_path):
    batch_id = match.get("XML_BATCH_ID", "")
    object_id = match["OBJECT_ID"]
    tax_year = match["TAX_PERIOD"][:4]
    zip_path = temp_path / f"{batch_id}.zip"

    if not batch_id:
        raise ValueError("IRS index row has no XML_BATCH_ID.")

    if not zip_path.exists():
        _download_zip_batch(match["SUB_DATE"], batch_id, zip_path)

    with zipfile.ZipFile(zip_path) as archive:
        xml_name = _find_xml_name(archive, object_id)

        try:
            xml_bytes = archive.read(xml_name)
        except NotImplementedError:
            xml_bytes = _extract_xml_with_system_tool(zip_path, xml_name)

    output_path = output_dir / f"{output_dir.name}_{tax_year}.xml"
    output_path.write_bytes(xml_bytes)
    return output_path


def _output_path_for_match(output_dir, match):
    tax_year = match["TAX_PERIOD"][:4]
    return output_dir / f"{output_dir.name}_{tax_year}.xml"


def _extract_xml_with_system_tool(zip_path, xml_name):
    extractors = [
        ("bsdtar", ["bsdtar", "-xOf", str(zip_path), xml_name]),
        ("7zz", ["7zz", "x", "-so", str(zip_path), xml_name]),
        ("7z", ["7z", "x", "-so", str(zip_path), xml_name]),
        ("unzip", ["unzip", "-p", str(zip_path), xml_name])
    ]

    last_error = None

    for executable, command in extractors:
        if not shutil.which(executable):
            continue

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True
            )
            return result.stdout
        except subprocess.CalledProcessError as error:
            last_error = error

    if last_error:
        raise last_error

    raise ValueError("No supported system ZIP extractor found.")


def _download_zip_batch(sub_date, batch_id, zip_path):
    candidates = [
        batch_id,
        batch_id.upper(),
        batch_id.lower()
    ]
    last_error = None

    for candidate in dict.fromkeys(candidates):
        zip_url = f"{IRS_XML_BASE_URL}/{sub_date}/{candidate}.zip"

        try:
            urllib.request.urlretrieve(zip_url, zip_path)
            return
        except (HTTPError, URLError) as error:
            last_error = error

    raise last_error


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


def _expand_years(value):
    value = (value or "").strip()

    if not value:
        return []

    years = []

    for part in value.split(","):
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start, end = part.split("-", 1)
            start_year = int(start)
            end_year = int(end)
            years.extend(range(start_year, end_year + 1))
        else:
            years.append(int(part))

    return [str(year) for year in sorted(set(years))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ein", required=True)
    parser.add_argument("--organization", required=True)
    parser.add_argument("--index-years", required=True)
    parser.add_argument("--tax-years", default="")
    parser.add_argument("--return-type", default="990PF")
    parser.add_argument("--skip-existing", action="store_true")

    args = parser.parse_args()

    files = download_irs_filings(
        ein=args.ein,
        organization=args.organization,
        index_years=args.index_years,
        tax_years=args.tax_years,
        return_type=args.return_type,
        skip_existing=args.skip_existing
    )

    for file in files:
        print(file)


if __name__ == "__main__":
    main()
