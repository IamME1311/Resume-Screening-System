# Resume Screening System

An automated resume screening tool that parses candidate resumes, extracts skills, experience, and keywords, and ranks them against a job description using a configurable weighted scoring model. Comes with both a **Streamlit web UI** and a **command-line interface**.

## Features

- **Multi-format parsing** — read resumes and job descriptions from `PDF`, `DOCX`, `DOC`, and `TXT` files, plus bulk resumes from a `JSONL` dataset.
- **Skill extraction** — a built-in skills taxonomy (programming languages, frameworks, databases, cloud, DevOps, web technologies, methodologies) with synonym matching.
- **Experience detection** — pulls years of experience from natural-language phrases and from employment date ranges.
- **Weighted scoring** — ranks candidates on required skills, preferred skills, experience, and keyword density.
- **Configurable weights & thresholds** — tune scoring via `data/config.json` without touching code.
- **Two interfaces** — an interactive Streamlit app and a scriptable CLI.
- **Exports** — download results as CSV or JSON, and the matched resumes themselves as a ranked ZIP.

## Project structure

```
.
├── app.py                       # Streamlit web application
├── main.py                      # Command-line interface
├── parsers/
│   ├── resume_parser.py         # Parse resumes (file/dir/JSONL) → text
│   └── jd_parser.py             # Parse job descriptions → required/preferred skills, experience
├── extractors/
│   └── keyword_extractor.py     # Extract skills, experience, keywords, contact info
├── matcher/
│   └── scorer.py                # Weighted scoring + ranking
├── data/
│   ├── config.json              # Scoring weights & thresholds
│   └── skills_taxonomy.json     # Skill → synonyms mapping
└── requirements.txt
```

## Requirements

- Python 3.10+ (uses `X | Y` type-union syntax)
- Dependencies (see `requirements.txt`):
  - `PyPDF2`, `python-docx` — file parsing
  - `streamlit`, `pandas` — web UI and tabular output

## Getting started

1. Clone the repo and enter the directory:
   ```powershell
   git clone https://github.com/IamME1311/Resume-Screening-System
   cd "Resume Screening System"
   ```

2. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Usage

### Web app (Streamlit)

```powershell
streamlit run app.py
```

Then in the browser:
1. Paste or upload a job description.
2. Upload one or more resume files (`PDF`, `DOCX`, `DOC`, `TXT`).
3. Set **Top N** matches and an optional **minimum score** in the sidebar.
4. Click **Start Screening Process** to view ranked candidates, score breakdowns, and export options.

### Command line

```powershell
# Screen resumes from a JSONL dataset, return top 10 (default)
python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl

# Screen resumes from a directory, return top 20
python main.py --jd data/job_description.txt --resumes resumes/ --top 20

# Apply a minimum score threshold
python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl --top 15 --min-score 60

# Output as JSON instead of CSV
python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl --format json
```

CLI options:

| Option | Description | Default |
| --- | --- | --- |
| `--jd` | Path to the job description file (required) | — |
| `--resumes` | Path to a resume directory or `.jsonl` file (required) | — |
| `--top` | Number of top matches to return | `10` |
| `--min-score` | Minimum score threshold (0–100) | none |
| `--format` | Output format: `csv` or `json` | `csv` |
| `--config` | Path to a custom config file | `data/config.json` |
| `--taxonomy` | Path to a custom skills taxonomy | `data/skills_taxonomy.json` |

Results are written to the `output/` directory with a timestamped filename.

## How scoring works

The total match score is a weighted combination of four components, each normalized to 0–100%:

| Component | Default weight | What it measures |
| --- | --- | --- |
| Required skills | 50% | Share of the JD's required skills found in the resume |
| Preferred skills | 25% | Share of the JD's preferred skills found in the resume |
| Experience | 15% | Resume's years of experience vs. the JD minimum (with tolerance) |
| Keyword density | 10% | Overlap of technical keywords, with a small frequency bonus |

Experience scoring is forgiving within a configurable tolerance: a candidate at or above the required years scores full marks, and those within the tolerance band receive a graduated score rather than a hard cutoff.

## Configuration

Edit `data/config.json` to adjust scoring behavior:

```json
{
  "weights": {
    "required_skills": 0.5,
    "preferred_skills": 0.25,
    "experience": 0.15,
    "keyword_density": 0.1
  },
  "min_score": 0.0,
  "experience_tolerance": 2,
  "default_top_n": 10
}
```

- **`weights`** — relative importance of each scoring component (should sum to 1.0).
- **`min_score`** — default minimum score threshold.
- **`experience_tolerance`** — years below the required minimum that still earn partial credit.
- **`default_top_n`** — default number of matches to return.

The skill vocabulary lives in `data/skills_taxonomy.json`, mapping a canonical skill name to a list of synonyms/variations. Add entries there to expand what the system recognizes.

## JSONL resume format

For bulk screening via the CLI, provide a `.jsonl` file with one JSON object per line. Recognized fields include:

```json
{"ResumeID": "R001", "Name": "Jane Doe", "Email": "jane@example.com", "Phone": "555-123-4567", "Category": "Backend", "Text": "...", "Experience": "...", "Skills": "...", "Summary": "...", "Education": "..."}
```

Text-bearing fields (`Text`, `Experience`, `Skills`, `Summary`, `Education`) are combined for matching.
