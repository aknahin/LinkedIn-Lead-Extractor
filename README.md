# LinkedIn Lead Extractor

A tool to extract public contact information (emails, phone numbers, LinkedIn URLs) for professionals from Google search results, focusing on LinkedIn profiles. No scraping of LinkedIn itself is performed; all data is gathered from Google's search snippets.

## Features
- **CLI and GUI**: Use either a command-line interface or a user-friendly graphical interface (Tkinter).
- **Google Custom Search API**: Utilizes the official API for reliable results.
- **Flexible Search**: Filter by job title, area/city, and email provider.
- **Export**: Results are saved as both Excel (`.xlsx`) and CSV (`.csv`) files.
- **Search History**: Keeps a log of previous extractions.

## Requirements
- Python 3.7+
- Packages: `requests`, `pandas`, `openpyxl` (for Excel export), `tkinter` (for GUI)

Install dependencies:
```bash
pip install requests pandas openpyxl
```
Tkinter is included with most Python installations.

## Setup
1. **Google Custom Search API**
   - Get an API key: https://developers.google.com/custom-search/v1/overview
   - Create a Custom Search Engine (CSE) and get the `cx` ID: https://cse.google.com/cse/all
2. **First Run**
   - Run the CLI script once to configure your API key and CSE ID:
     ```bash
     python lead_extractor_cli.py
     ```
   - You will be prompted to enter your API key and CSE ID. This creates `google_search_config.json`.

## Usage

### Command-Line Interface
Run:
```bash
python lead_extractor_cli.py
```
You will be prompted for:
- Job title (e.g., realtor)
- Area/city (e.g., Phoenix)
- Number of contacts to extract
- Email provider (e.g., gmail.com)

Results are saved in the current directory as both `.xlsx` and `.csv` files.

### Graphical User Interface
Run:
```bash
python lead_extractor_gui.py
```
- Fill in the fields and click "Start Extraction".
- Progress and results are shown in the log area.
- Files are saved in the current directory.

## Notes
- **No LinkedIn scraping**: This tool does not violate LinkedIn's terms of service.
- **Quota limits**: The Google API has daily limits. If you hit a quota, wait or use a different API key.
- **Accuracy**: Results depend on the information available in Google search snippets.

## License
See `LICENSE` file.

## Author
- AK Nahin — [aknahin.com](https://aknahin.com)
