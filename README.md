# Personal Finance Intelligence

A personal finance dashboard that:
- Ingests your expense CSV (raw data)
- Cleans & feature-engineers it into an analytics-ready dataset (processed data)
- Computes monthly metrics (spend, savings, category shares, growth, weekend vs weekday)
- Generates automated insights and recommendations
- Lets you log daily expenses and instantly refresh the dashboard

> **Note**: This repository deliberately excludes `ProjectRules.md` and contains no `graphify` references.

---

## Features

### 1) Data pipeline
- Reads `data/raw/personal_expenses.csv`
- Produces `data/processed/cleaned_expenses.csv`
- Adds engineered fields such as:
  - `month`, `month_name`, `day_of_week`, `is_weekend`
  - `cumulative_spent` (burn rate within each calendar month)

### 2) Dashboard (Streamlit)
Built in `app/main.py`.

Tabs:
- **Goal Setup**: set monthly salary and savings goal (%)
- **Recommendations**: choose a month and view metrics, insights and recommendations
- **Daily Log**: add a transaction (updates raw CSV, rebuilds processed data, reruns)

### 3) Analytics
Located in `src/`:
- `src/processor.py`: cleaning + feature engineering
- `src/analytics.py`: monthly summaries, growth, category shares, weekend factor, health score
- `src/insights.py`: converts metrics into human-readable insight text
- `src/recommender.py`: generates actionable recommendations from metric summaries

---

## Project structure

- `app/`
  - `main.py` (Streamlit entry point)
- `src/`
  - `processor.py` (data cleaning/features)
  - `analytics.py` (metric computation)
  - `insights.py` (insight generation)
  - `recommender.py` (recommendation engine)
- `data/`
  - `raw/` (input CSV)
  - `processed/` (generated CSV)
  - `samples/` (sample CSVs, if present)
- `notebook/` (EDA artifacts)

---

## Setup

### 1) Python requirements
This project uses the dependencies in `requirements.txt`.

```bash
python -m venv .venv
# Windows:
# .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Verify raw CSV schema
The dashboard expects `data/raw/personal_expenses.csv` to contain (at least) these columns:
- `date` (parseable date strings)
- `amount` (expense amount)
- `category`
- optionally `payment_mode`, `description`

The app also treats monthly salary as an income value and uses it to compute savings metrics.

---

## Running the app

```bash
streamlit run app/main.py
```

The app:
1. Rebuilds processed data from raw on startup
2. Loads default salary from the first row’s `income` (if available)
3. Lets you log daily expenses and updates both raw and processed datasets

---

## How recommendations work (high level)

Recommendations are computed from the monthly summary:
- Category shares (percentage of total spend)
- Income, total spent, savings gap, target savings

The recommender then:
- Alerts when key categories exceed benchmark percentage limits
- Produces a goal-gap message (amount needed to reach target savings)
- Suggests the most impactful lever based on the largest excess

---

## Datasets and rebuild behavior

- The Streamlit app rebuilds `data/processed/cleaned_expenses.csv` from the raw CSV via `clean_and_feature_engineer()`.
- The **Daily Log** writes a new row to `data/raw/personal_expenses.csv` and triggers a rebuild so the **Recommendations** tab always reflects the latest data.

---

## Troubleshooting

### Common issues
- **Date parsing errors**: ensure `date` values are in a consistent format parseable by pandas.
- **Empty processed data**: confirm `data/raw/personal_expenses.csv` is non-empty and includes valid dates.

---

## License

Add your preferred license here (MIT/Apache-2.0/etc.) if applicable.

