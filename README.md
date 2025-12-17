# Lead Generation System (Scientific BD Intelligence)

Lead discovery and enrichment pipeline for identifying and scoring researchers and decision-makers in the **3D in‑vitro models** and **drug safety / toxicology** space.

## Live Demo

https://88uqgjjhbdcbbcfz3nykmw.streamlit.app/

This repository focuses on **real-data enrichment** (no fabricated lead details). When an attribute cannot be reliably sourced (e.g., business email without a verified domain), it is left empty rather than guessed.

---

## Key Features

- **ORCID discovery** for researcher profiles
- **PubMed enrichment** for publications and author affiliations (when available)
- **Company research** (official website/domain discovery via SerpAPI)
- **Email enrichment** (Hunter.io) using real domains only
- **Location normalization** and biotech hub tagging
- **Propensity scoring** based on multiple real signals
- **Streamlit dashboard** to run the pipeline, filter results, and export CSV

---

## Architecture (High-Level)

- **Pipeline orchestration**: `data_pipeline/main_pipeline.py`
- **Scrapers**:
  - ORCID: `data_pipeline/scrapers/orcid_scraper.py`
  - PubMed: `data_pipeline/scrapers/pubmed_scraper.py`
  - Funding: `data_pipeline/scrapers/funding_scraper.py`
  - Conferences (placeholder): `data_pipeline/scrapers/conference_scraper.py`
- **Enrichment**:
  - Company research: `data_pipeline/enrichment/company_research.py`
  - Email finding: `data_pipeline/enrichment/email_finder.py`
  - Location analysis: `data_pipeline/enrichment/location_analyzer.py`
- **Scoring**: `data_pipeline/scoring/propensity_scorer.py`
- **Dashboard**: `data_pipeline/dashboard/streamlit_dashboard.py`

---

## Setup

### Requirements

- Python 3.9+ recommended

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

The pipeline loads keys from `.env` (via `python-dotenv`).

---

## API Keys (What You Need for Accurate Results)

### Required (for best results)

- **SerpAPI** (`SERP_API_KEY`)
  - Used for:
    - discovering official company websites/domains
    - fallback researcher/company/location discovery when ORCID/PubMed is sparse
- **Hunter.io** (`EMAIL_API_KEY`)
  - Used for:
    - email discovery and verification once a trusted domain is available

### Optional (improves quality)

- **ORCID Auth** (`ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET`)
  - Improves ORCID access; public ORCID often returns limited profile fields
- **PubMed API key** (`PUBMED_API_KEY`) + `PUBMED_EMAIL`
  - Increases rate limits and improves reliability
- **Google Maps** (`GOOGLE_MAPS_API_KEY`)
  - More reliable geocoding/normalization for location analysis

---

## Usage

### Option A: Streamlit Dashboard (Recommended)

```bash
streamlit run data_pipeline/dashboard/streamlit_dashboard.py
```

In the UI you can:

- run the pipeline
- filter by score and enrichment completeness (email/company/location/biotech hub)
- export filtered results as CSV

### Option B: CLI Runner

```bash
python run_pipeline.py
```

---

## Output

The dashboard and CSV export typically include:

- `Name`
- `Title`
- `Company`
- `Location`
- `Email`
- `Score`
- `ORCID ID`, `ORCID URL`
- `Company Domain`, `Company Website`
- `Email Source`, `Email Confidence`, `Email Verified`
- `Biotech Hub`, `Biotech Hub Name`

---

## Scoring (Propensity Score)

The propensity score is computed from multiple real signals such as:

- title relevance
- publication activity (if found)
- location quality / biotech hub
- company presence
- email availability
- company signals from research

Scores will remain low when upstream data is missing (e.g., public ORCID profiles without employment/address, no PubMed hits, or no company domain).

---

## Known Limitations (Important)

- **Public ORCID profiles can be sparse**: employment, address, and other details are often private or incomplete.
- **PubMed may return 0 results** depending on keywords, name ambiguity, or query constraints.
- **Business email accuracy depends on access to the right email data sources**:
  - This project currently uses **Hunter.io** and requires a **verified company domain**.
  - I did not find (or integrate) the “perfect” business-email APIs/data providers for every organization and region.
  - If I obtain stronger business email data provider access (and their APIs/credits), the system can be made significantly better and more complete.

---

## Security Notes

- Put keys in `.env` and **do not commit** them.
- If any keys were previously committed, rotate them immediately.

---

## Roadmap

- Better entity resolution (matching the same person across ORCID/PubMed/web)
- Stronger affiliation extraction from web sources
- Additional email providers (as API access becomes available)
- Conference scraping implementations

---

## License

This project is for demonstration and educational use.

