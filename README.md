# Grants Pipeline

Turn IRS foundation grant XML filings into formatted Excel workbooks.

The pipeline extracts recipient grants from IRS XML, builds summary tables, categorizes grants, and saves one workbook per organization with one sheet per filing year.

## What It Produces

For each organization, output is saved as:

```text
output/<organization>/<organization>.xlsx
```

Each year is written as its own sheet:

```text
output/firedoll/firedoll.xlsx
├── 2021
├── 2022
├── 2023
├── 2024
└── 2025
```

Rerunning the same year replaces that year sheet instead of creating duplicates.

## Workbook Tables

Each generated sheet includes:

- Master grants table
- Grant statistics
- Unique grant amounts
- Grants by amount range
- Location distribution
- Category distribution
- State/city distribution

The workbook is formatted for spreadsheet review with compact table placement, currency formatting, percentage formatting, alternating row fills, and highlighted headers/totals.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tanay-jaiman/grants_pipeline.git
cd grants_pipeline
```

### 2. Install `fzf`

The interactive runner uses `fzf`.

macOS:

```bash
brew install fzf
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install fzf
```

### 3. Run Setup

```bash
./install.sh
```

This creates a virtual environment, installs Python dependencies, creates `input/` and `output/`, and adds a `grants-pipeline` shell alias.

Reload your shell config after setup:

```bash
source ~/.zshrc
```

or, if you use Bash:

```bash
source ~/.bashrc
```

## Input Layout

Place XML files inside organization folders under `input/`:

```text
input/
└── firedoll/
    ├── firedoll_2021.xml
    ├── firedoll_2022.xml
    ├── firedoll_2023.xml
    ├── firedoll_2024.xml
    └── firedoll_2025.xml
```

The year is inferred from the first four-digit year in the filename.

## Usage

Run the interactive workflow:

```bash
grants-pipeline
```

Then:

1. Select an organization folder.
2. Confirm or override the organization name.
3. Choose `Single XML file`, `All XML files in folder`, or `Download IRS XML by EIN`.
4. Confirm or override the inferred year when prompted.

### Single File Example

Choose:

```text
input/firedoll
Single XML file
firedoll_2025.xml
```

This writes or replaces the `2025` sheet in:

```text
output/firedoll/firedoll.xlsx
```

### Batch Example

Choose:

```text
input/firedoll
All XML files in folder
```

This processes every `.xml` file in that folder and writes one sheet per year.

### Download IRS XML by EIN

Choose:

```text
input/firedoll
Download IRS XML by EIN
```

Then enter:

- EIN
- IRS index filing year, such as `2025`
- Optional tax year filter, such as `2024`
- Return type, usually `990PF` for private foundations

The downloader reads the official IRS yearly XML index, finds matching filings, downloads the relevant IRS XML ZIP batch, extracts the matching XML object, and saves it under:

```text
input/<organization>/<organization>_<tax_year>.xml
```

After downloading, run `grants-pipeline` again and choose `Single XML file` or `All XML files in folder` to generate the workbook.

## Direct CLI Usage

You can also run the pipeline directly:

```bash
python3 main.py \
  --xml input/firedoll/firedoll_2025.xml \
  --organization firedoll \
  --year 2025
```

Download IRS XML directly:

```bash
python3 -m src.irs_download \
  --ein 123456789 \
  --organization example_foundation \
  --index-year 2025 \
  --tax-year 2024 \
  --return-type 990PF
```

## Configuring Categories

Grant categories are configured in `src/config.py`:

```python
CATEGORIES = [
    "Education & Youth Development",
    "Community Empowerment",
    "Arts, Culture, and Social Impact",
    "Immigration Support"
]
```

The categorizer checks:

1. The grant purpose.
2. The recipient organization name.
3. `Other`, if neither matches.

Category matching is keyword-based. The configured category names provide the main signal, and `src/grant_search.py` expands common related terms such as `education -> school/student/youth` or `immigration -> asylum/refugee/migrant`.

## Notes

- `input/`, `output/`, virtual environments, generated spreadsheets, and private TODO notes are ignored by git.
- XML files may be modified by the cleaner before parsing, so keep a separate raw copy if you need the original untouched filing.
- IRS XML files are found through yearly filing indexes. The index year is the IRS posting year, which may be later than the tax period year.
- Google Sheets can reinterpret native Excel table styles, so the exporter uses plain cell formatting instead of embedded Excel table objects.
