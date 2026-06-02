# Backlink Tool – Automated Backlink Submission

A terminal-based tool that automates backlink research and submission for your product across directory sites and listing platforms.

## Features

- **Competitor Research** — Query backlink sources from a competitor domain via Ahrefs scraping
- **Auto Submission** — Batch-submit your product to up to 20 sites at a time using Playwright browser automation
- **Full Pipeline** — Research → Submit in one workflow
- **Backlink Tracking** — Monitor submitted sites and get desktop notifications when your link goes live
- **Product Manager** — Configure your product info and upload images before submitting
- **Excel Reports** — Auto-generate `.xlsx` reports for research results and submission history

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in your Google account (used for sites that require Google login):

```bash
cp .env.example .env
```

```env
GOOGLE_EMAIL=your-email@example.com
GOOGLE_PASSWORD=your-password
```

### 3. Run

```bash
python main.py
```

Or double-click `启动工具.bat` on Windows.

## Menu Options

| Option | Description |
|--------|-------------|
| `[1]` Backlink Research | Enter a competitor domain, scrape their backlink sources |
| `[2]` Direct Submit | Paste up to 20 domains and auto-submit your product |
| `[3]` Full Pipeline | Research a competitor then immediately submit to those sites |
| `[4]` Backlink Tracking | Check if submitted sites have indexed your link; desktop alert on go-live |
| `[5]` Product Setup | Set your product name, URL, description, keywords, and images |

## Tech Stack

- Python 3.10+
- [Playwright](https://playwright.dev/python/) — headless browser automation
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel report generation
- [plyer](https://plyer.readthedocs.io/) — desktop notifications

## Output Files

| File | Description |
|------|-------------|
| `output/product.json` | Your product configuration |
| `output/submissions.json` | Submission history and tracking status |
| `output/*.xlsx` | Auto-generated research and submission reports |