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
- State/city distribution with grant counts and total amount by state

The workbook is formatted for spreadsheet review with compact table placement, currency formatting, percentage formatting, alternating row fills, and highlighted headers/totals.

Grant amount ranges are generated from the data instead of using one fixed bucket size. Balanced filings use readable equal-width ranges, while filings with very small and very large grants use compact money-scale ranges so outliers do not collapse the smaller grants into one oversized bucket.

The location distribution table is sorted by percentage of total amount distributed. The state/city table is sorted by number of grants, then total amount, so the most relevant states appear first.

## Quick Start

These steps take a new user from a fresh clone to a generated workbook.

### 1. Clone the Project

Open a terminal and run:

```bash
git clone https://github.com/tanay-jaiman/grants_pipeline.git
cd grants_pipeline
```

### 2. Install Everything

```bash
./install.sh
```

This does the first-time setup:

- Creates `venv/`.
- Installs Python dependencies.
- Creates `input/` and `output/`.
- Creates a local `.env` file if one does not already exist.
- Adds a `grants-pipeline` shell alias.

Reload your shell after setup:

```bash
source ~/.zshrc
```

If you use Bash:

```bash
source ~/.bashrc
```

### 3. Add an Optional Geocoding Key

Distance labels work without an API key, but first runs are slower. For faster distance-label geocoding, open `.env` and paste your OpenRouteService key:

```text
OPENROUTESERVICE_API_KEY=your-api-key
GOOGLE_MAPS_API_KEY=
```

The `.env` file is local-only and ignored by git.

### 4. Run the App

```bash
grants-pipeline
```

Use the arrow keys to move, Enter to select, and `q` to cancel.

### 5. Start a New Project

Choose:

```text
Start a new project
```

Then enter:

```text
Project/organization name: firedoll
EIN: 94-3301999
Tax year(s), e.g. 2021-2025: 2021-2025
IRS index filing year(s): 2021-2026
Return type: 990PF
```

The app downloads matching IRS XML filings, saves them under `input/<organization>/`, and generates the workbook.

### 6. Find the Output

The finished workbook is saved here:

```text
output/<organization>.xlsx
```

Each tax year becomes its own worksheet. Newer years are processed first so the latest sheet appears first.

### 7. Work With Existing XML Files

If you already have XML files, place them like this:

```text
input/
└── example_foundation/
    ├── example_foundation_2025.xml
    ├── example_foundation_2024.xml
    └── example_foundation_2023.xml
```

Then run:

```bash
grants-pipeline
```

Choose:

```text
Work on an existing project
All XML files in input/example_foundation
```

The app processes XML files newest-to-oldest and writes one workbook at `output/example_foundation.xlsx`.

## What Setup Creates

After installation, the project has these local working files and folders:

```text
grants_pipeline/
├── .env
├── input/
├── output/
└── venv/
```

These are ignored by git, so user data, API keys, XML files, caches, and generated spreadsheets stay local.

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

## Usage Reference

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

## Configuring Amount Ranges

The range table is automatic by default. You can tune the behavior in `src/config.py`:

```python
RANGE_STEP_OVERRIDE = None
RANGE_TARGET_BUCKETS = 10
RANGE_MIN_BUCKETS = 5
RANGE_MAX_BUCKETS = 12
RANGE_MIN_NICE_BOUNDARY = 1000
```

Set `RANGE_STEP_OVERRIDE` to a number such as `5000` or `25000` when you want fixed-width buckets for a specific presentation style. Leave it as `None` for smart ranges.

## Optional Distance Labels

The state/city table can annotate cities with distance from the geographic center of that state:

```text
Berkeley (201 mi), Oakland (196 mi)
```

Distances use a lightweight two-step lookup:

- Geocode the city once.
- Calculate straight-line distance from the state center to the city locally.

By default, the pipeline uses free public OpenStreetMap/Nominatim geocoding with a polite delay. For faster geocoding, set an OpenRouteService API key. Google Geocoding is also supported as a fallback if `GOOGLE_MAPS_API_KEY` is set.

```bash
export OPENROUTESERVICE_API_KEY="your-api-key"
export GOOGLE_MAPS_API_KEY="your-api-key"
grants-pipeline
```

You can also store keys in a local `.env` file:

```text
OPENROUTESERVICE_API_KEY=your-api-key
GOOGLE_MAPS_API_KEY=your-api-key
```

`.env` is ignored by git and loaded automatically when distance labels are generated.

The cache is a small local SQLite file:

```text
input/.distance_cache.sqlite
```

Because `input/` is ignored by git, cached API results stay local and are not shared with the repo. Older JSON caches are migrated automatically when the SQLite cache is first created. You can tune the safety limits in `src/config.py`:

```python
DISTANCE_MAX_UNCACHED_ELEMENTS_PER_RUN = 50
DISTANCE_REQUEST_DELAY_SECONDS = 1.1
```

The limiter counts only uncached city coordinate lookups. Cached distances do not call external services again. If a run needs more uncached lookups than the configured cap, the remaining cities are left as plain names and the pipeline prints a warning.

## Notes

- `input/`, `output/`, virtual environments, generated spreadsheets, and private TODO notes are ignored by git.
- XML files may be modified by the cleaner before parsing, so keep a separate raw copy if you need the original untouched filing.
- IRS XML files are found through yearly filing indexes. The index year is the IRS posting year, which may be later than the tax period year.
- Google Sheets can reinterpret native Excel table styles, so the exporter uses plain cell formatting instead of embedded Excel table objects.
