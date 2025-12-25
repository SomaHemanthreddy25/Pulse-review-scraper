# Review Scraper (G2, Capterra, TrustRadius)

This project scrapes product reviews from G2, Capterra, and TrustRadius for a specified company and date range.

## Features

- **Multi-Source**: Scrapes G2, Capterra, and TrustRadius.
- **Date Filtering**: Collects reviews strictly within the provided start and end dates.
- **JSON Output**: Exports structured data including Title, Description, Date, Source, and (optional) Rating.
- **Headless Browser**: Uses Playwright for robust handling of dynamic content (SPA, endless scroll).
- **Capterra ID Resolution**: Automatically searches for Capterra product IDs.

## Prerequisites

- Python 3.8+
- Playwright

## Installation

1.  **Clone/Download the repository**.
2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright browsers**:
    ```bash
    playwright install
    ```

## Usage

Run the script from the command line:

```bash
python main.py --company "Company Name" --start_date YYYY-MM-DD --end_date YYYY-MM-DD --source [g2|capterra|trustradius|all]
```

### Examples

**Scrape Slack reviews from all sources for Jan 2023:**
```bash
python main.py --company "Slack" --start_date 2023-01-01 --end_date 2023-01-31 --source all
```

**Scrape Asana reviews from G2 only (Debug mode/Visible browser):**
```bash
python main.py --company "Asana" --start_date 2023-01-01 --end_date 2023-12-31 --source g2 --no-headless
```

## Bonus Implementation

- **Third Source**: Integrated **TrustRadius** as the third source specializing in SaaS reviews.
- **Capterra Search**: Implemented a search-first approach for Capterra to handle their ID-based URL structure automatically.

## Notes & Limitations

- **Anti-Bot Measures**: G2 and Capterra have strong Cloudflare protections. If the script fails or hangs on "Just a moment", try running with `--no-headless` or on a different network.
- **Date Parsing**: Date formats vary by region and over time on these platforms. The script attempts to parse common formats but may require updates if site layouts change.
- **Performance**: Scraping is done sequentially for stability.

## GitHub Upload Instructions

Since you are running this locally, follow these steps to upload to GitHub:

1.  **Install Git**: Download and install from [git-scm.com](https://git-scm.com/).
2.  **Create Repo**: Create a new repository on GitHub named `pulse-review-scraper`.
3.  **Run Commands**: Open your terminal in this folder and run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SomaHemanthreddy25/pulse-review-scraper.git
git push -u origin main
```



