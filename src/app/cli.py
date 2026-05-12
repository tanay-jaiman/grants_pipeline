#!/usr/bin/env python3

import curses
import json
import re
import subprocess
import sys
from pathlib import Path

from src.app.setup import ensure_prerequisites
from src.ingest.irs_download import download_irs_filings


INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


def main():
    _print_header()
    _ensure_base_dirs()

    choice = _choose(
        "What would you like to do?",
        [
            "Start a new project",
            "Work on an existing project"
        ]
    )

    if choice == "Start a new project":
        _start_new_project()
    else:
        _work_on_existing_project()


def _start_new_project():
    project_name = _prompt_required("Project/organization name")
    project_slug = _safe_name(project_name)
    project_dir = INPUT_DIR / project_slug
    project_dir.mkdir(parents=True, exist_ok=True)
    metadata = _load_project_metadata(project_dir)
    metadata.update({
        "name": project_name,
        "slug": project_slug
    })
    _save_project_metadata(project_dir, metadata)

    print(f"\nCreated input folder for {project_slug}.")

    downloaded_files = _download_filings(project_dir, metadata)

    if downloaded_files:
        _process_files(downloaded_files, project_slug)
    else:
        print("\nNo XML files were downloaded, so no workbook was generated.")


def _work_on_existing_project():
    project_dirs = sorted(path for path in INPUT_DIR.iterdir() if path.is_dir())

    if not project_dirs:
        print("\nNo existing projects found in input/. Start a new project first.")
        return

    project_dir = _choose("Select a project folder:", project_dirs)
    project_name = project_dir.name
    metadata = _load_project_metadata(project_dir)
    xml_files = _sort_xml_files_latest_first(project_dir.glob("*.xml"))

    if not xml_files:
        print(f"\nNo XML files found in {project_dir}.")

        if _confirm("Download IRS XML files now?"):
            downloaded_files = _download_filings(project_dir, metadata)
            _process_files(downloaded_files, project_name)

        return

    target = _choose(
        "What would you like to do?",
        [
            "Download missing IRS XML files",
            f"All XML files in {project_dir}",
            "Choose one XML file"
        ]
    )

    if target == "Download missing IRS XML files":
        downloaded_files = _download_filings(
            project_dir,
            metadata,
            skip_existing=True
        )

        if downloaded_files and _confirm("Generate spreadsheet sheets for new downloads?"):
            _process_files(downloaded_files, project_name)
    elif target.startswith("All XML"):
        _process_files(xml_files, project_name)
    else:
        xml_file = _choose("Select an XML file:", xml_files)
        _process_files([xml_file], project_name)


def _download_filings(project_dir, metadata, skip_existing=False):
    project_name = project_dir.name
    print("\nIRS XML Download")
    ein = _prompt_with_default("EIN", metadata.get("ein", ""), required=True)
    tax_years = _prompt_with_default(
        "Tax year(s), e.g. 2021-2025",
        metadata.get("tax_years", "")
    )
    default_index_years = _default_index_years(tax_years)
    index_years = _prompt_with_default(
        "IRS index filing year(s)",
        metadata.get("index_years", default_index_years) or default_index_years
    )
    return_type = _prompt_with_default(
        "Return type",
        metadata.get("return_type", "990PF") or "990PF"
    )

    metadata.update({
        "ein": ein,
        "tax_years": tax_years,
        "index_years": index_years,
        "return_type": return_type
    })
    _save_project_metadata(project_dir, metadata)

    print("\nDownloading IRS XML filings...")

    try:
        files = download_irs_filings(
            ein=ein,
            organization=project_name,
            index_years=index_years,
            tax_years=tax_years,
            return_type=return_type,
            skip_existing=skip_existing
        )
    except ValueError as error:
        print(f"\n{error}")
        return []

    if files:
        print("\nDownloaded:")

        for file in files:
            print(f"  - {file}")

    return files


def _load_project_metadata(project_dir):
    metadata_path = project_dir / "project.json"

    if not metadata_path.exists():
        return {}

    try:
        return json.loads(metadata_path.read_text())
    except json.JSONDecodeError:
        print(f"\nCould not parse {metadata_path}; starting with blank metadata.")
        return {}


def _save_project_metadata(project_dir, metadata):
    metadata_path = project_dir / "project.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )


def _process_files(xml_files, organization):
    for xml_file in _sort_xml_files_latest_first(xml_files):
        year = _infer_year(xml_file)

        if not year:
            year = _prompt_required(f"Year for {xml_file}")

        print(f"\nProcessing {xml_file}")
        print(f"Organization: {organization}")
        print(f"Year: {year}")

        subprocess.run(
            [
                sys.executable,
                "main.py",
                "--xml",
                str(xml_file),
                "--organization",
                organization,
                "--year",
                year
            ],
            check=True
        )


def _choose(prompt, options):
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            return curses.wrapper(_choose_with_arrows, prompt, options)
        except curses.error:
            pass

    return _choose_with_numbers(prompt, options)


def _choose_with_arrows(screen, prompt, options):
    selected = 0
    top = 0

    curses.curs_set(0)
    screen.keypad(True)

    while True:
        screen.clear()
        height, width = screen.getmaxyx()
        visible_count = max(1, height - 5)

        screen.addstr(0, 0, prompt[:width - 1], curses.A_BOLD)
        screen.addstr(
            1,
            0,
            "Use ↑/↓ to move, Enter to select, q to cancel"[:width - 1]
        )

        if selected < top:
            top = selected
        elif selected >= top + visible_count:
            top = selected - visible_count + 1

        visible_options = options[top:top + visible_count]

        for row, option in enumerate(visible_options, start=3):
            option_index = top + row - 3
            label = f"> {option}" if option_index == selected else f"  {option}"
            style = curses.A_REVERSE if option_index == selected else curses.A_NORMAL
            screen.addstr(row, 0, str(label)[:width - 1], style)

        screen.refresh()
        key = screen.getch()

        if key in (curses.KEY_UP, ord("k")):
            selected = max(0, selected - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            selected = min(len(options) - 1, selected + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            return options[selected]
        elif key in (27, ord("q")):
            raise SystemExit("Cancelled.")


def _choose_with_numbers(prompt, options):
    print(f"\n{prompt}")

    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")

    while True:
        choice = input("Choose a number: ").strip()

        if choice.isdigit():
            choice_index = int(choice)

            if 1 <= choice_index <= len(options):
                return options[choice_index - 1]

        print("Please enter one of the listed numbers.")


def _confirm(prompt):
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def _prompt_required(prompt):
    while True:
        value = input(f"{prompt}: ").strip()

        if value:
            return value

        print("This value is required.")


def _prompt_with_default(prompt, default="", required=False):
    label = f"{prompt} [{default}]" if default else prompt

    while True:
        value = input(f"{label}: ").strip() or default

        if value or not required:
            return value

        print("This value is required.")


def _infer_year(xml_file):
    match = re.search(r"([0-9]{4})", Path(xml_file).name)
    return match.group(1) if match else ""


def _sort_xml_files_latest_first(xml_files):
    return sorted(
        xml_files,
        key=lambda xml_file: (
            int(_infer_year(xml_file) or 0),
            Path(xml_file).name
        ),
        reverse=True
    )


def _default_index_years(tax_years):
    if re.fullmatch(r"[0-9]{4}-[0-9]{4}", tax_years):
        start, end = tax_years.split("-", 1)
        return f"{start}-{int(end) + 1}"

    if re.fullmatch(r"[0-9]{4}", tax_years):
        return f"{tax_years}-{int(tax_years) + 1}"

    return "2021-2026"


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_").lower()


def _ensure_base_dirs():
    ensure_prerequisites()


def _print_header():
    print("\nGrants Pipeline")
    print("================")
    print("Download IRS XML filings and generate grant analysis workbooks.")


if __name__ == "__main__":
    main()
