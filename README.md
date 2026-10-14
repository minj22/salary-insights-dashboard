# Developer Pay Insights

A client-facing Streamlit dashboard presenting the MIE1624 Assignment 1 analysis of the
2025 Stack Overflow Developer Survey: role-level satisfaction and pay, remote vs. hybrid
salaries, and the education pay premium in the US and Canada.

## Files

| File | Purpose |
|---|---|
| `app.py` | The dashboard (Streamlit + Plotly). Reads only `data/`. |
| `data/summary.json` | Every statistic, table and test result shown in the app. |
| `data/bootstrap.npz` | Bootstrap replicate statistics (resampled means, medians, t and F values). |
| `build_data.py` | Regenerates `data/` from the raw CSV using the notebook's exact code and seeds. |
| `.streamlit/config.toml` | Navy / indigo / white theme. |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Rebuild the aggregated data (optional)

Needs `pandas`, `numpy` and `scipy` installed, plus the course CSV. Use the same library
versions as the notebook (pandas 3.0.1, numpy 2.5.4, scipy 1.17.0) so the seeded bootstrap
results are reproduced exactly.

```bash
python build_data.py /path/to/clean_stackoverflow_data.csv
```

## Deploy to Streamlit Community Cloud

1. Push this folder to a **public** GitHub repository. Do **not** commit the raw CSV.
2. At share.streamlit.io choose **Create app**, select the repository, and set the main
   file to `app.py`.
3. Open the resulting URL in a private/incognito window to confirm it loads without a login.

## Data privacy

The dashboard is public, so it contains aggregated results only. The salary-vs-age view
uses binned counts, box plots use five-number summaries, and no individual survey
response is included.
