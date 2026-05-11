# Grants Pipeline

Turn IRS foundation grant XML filings into formatted Excel workbooks.

The pipeline extracts recipient grants from IRS XML, builds summary tables, categorizes grants, and saves one workbook per organization with one sheet per filing year.

## What It Produces

For each organization, output is saved as:

```text
output/<organization>.xlsx
```

Each year is written as its own sheet:

```text
output/firedoll.xlsx
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

### 2. Run Setup

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
    ├── project.json
    ├── firedoll_2021.xml
    ├── firedoll_2022.xml
    ├── firedoll_2023.xml
    ├── firedoll_2024.xml
    └── firedoll_2025.xml
```

The year is inferred from the first four-digit year in the filename.

Each project folder can include `project.json`, which stores reusable project metadata:

```json
{
  "ein": "94-3301999",
  "index_years": "2021-2026",
  "name": "Firedoll Foundation",
  "return_type": "990PF",
  "slug": "firedoll",
  "tax_years": "2021-2025"
}
```

The interactive workflow creates and updates this file automatically. Existing projects reuse saved values, so you do not need to re-enter the EIN every time.

## Usage

Run the interactive workflow:

```bash
grants-pipeline
```

Use the arrow keys to move through menus, press Enter to select, and press `q` to cancel.

Then:

1. Choose `Start a new project` or `Work on an existing project`.
2. For a new project, enter the organization name, EIN, tax years, and return type. The app downloads available IRS XML files and generates the workbook.
3. For an existing project, select a folder, download missing IRS XML files, or regenerate a single XML file. Folder runs regenerate only the year sheets for XML files in that folder.
4. Confirm any year that cannot be inferred from the XML filename.

### Single File Example

Choose `Work on an existing project`, then:

```text
input/firedoll
Choose one XML file
firedoll_2025.xml
```

This writes or replaces the `2025` sheet in:

```text
output/firedoll.xlsx
```

### Batch Example

Choose `Work on an existing project`, then:

```text
input/firedoll
All XML files in input/firedoll
```

This processes every `.xml` file in that folder and writes one sheet per year.

### Download Missing XML for an Existing Project

Choose `Work on an existing project`, select the project folder, then choose:

```text
Download missing IRS XML files
```

Saved metadata is used as the default for EIN, return type, and year ranges. Existing local files such as `input/firedoll/firedoll_2024.xml` are skipped, so only missing years are downloaded.

### Download IRS XML by EIN

Choose `Start a new project`, then enter:

```text
Project/organization name: firedoll
EIN: 94-3301999
Tax year(s): 2021-2025
IRS index filing year(s): 2021-2026
Return type: 990PF
```

The downloader reads the official IRS yearly XML index, finds matching filings, downloads the relevant IRS XML ZIP batch, extracts the matching XML object, saves it under:

```text
input/<organization>/<organization>_<tax_year>.xml
```

and then generates the workbook.

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
  --index-years 2021-2026 \
  --tax-years 2021-2025 \
  --return-type 990PF \
  --skip-existing
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
