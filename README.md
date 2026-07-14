# Mortgage Denial Risk Pipeline | NC & VA 2024

## Overview

In Econ 101, I became fascinated by the interplay between macroeconomic policy and individual financial outcomes. Learning how Federal Reserve rate decisions ripple through bank lending behavior — affecting credit availability, mortgage rates, and ultimately whether a family can buy a home — made me want to explore this relationship empirically. Specifically, I wanted to test whether macroeconomic indicators like unemployment rates and housing price indices have meaningful predictive power over loan denial alongside the individual-level financial factors that traditionally drive underwriting decisions.

To answer this, I built an end-to-end data pipeline on 2024 HMDA mortgage application data for North Carolina and Virginia, enriched with state-level macroeconomic indicators from the Federal Reserve Economic Data (FRED) API, and trained a logistic regression model to predict loan denial.

**Tableau Dashboard:** [HMDA Mortgage Lending Risk Analysis](https://public.tableau.com/views/Book1_17836189059930/Dashboard1)

---

## Key Findings

- **Loan-to-value ratio is the strongest predictor of denial** — by a significant margin, confirming that the proportion of the property being financed matters more than the absolute loan size or income level alone.
- **Macroeconomic indicators added predictive signal but did not dominate** — state unemployment rate and house price index contribute to the model, but individual loan characteristics remain the primary drivers of denial decisions.
- **Racial disparities in denial rates persist in the data** — Black and African American applicants face denial rates approximately 20 percentage points higher than Asian applicants. Importantly, the model was trained exclusively on financial factors, meaning this disparity exists independent of the features the model used — a finding consistent with fair lending research on HMDA data.
- **Loan purpose significantly affects denial likelihood** — home purchase applications are denied at roughly 9%, while home improvement and cash-out refinancing exceed 30%. This suggests lenders apply meaningfully different risk standards by loan type.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Pipeline orchestration, data ingestion, modeling |
| DuckDB | In-process SQL analytics engine for data storage and transformation |
| SQL | Multi-stage transformation layer (cleaning, feature engineering, joins) |
| FRED API | Macroeconomic indicator ingestion |
| scikit-learn | Logistic regression, train/test split, standard scaling, evaluation |
| Tableau Public | Interactive dashboard |
| Git/GitHub | Version control |

---

## Pipeline Architecture

```
[1. INGEST]
Raw HMDA CSV (844k rows, NC & VA 2024) + FRED API pulls
(state unemployment, state HPI, national mortgage rate)
→ loaded into DuckDB, raw CSVs saved to data/raw/

[2. CLEAN — 01_clean.sql]
Filter to final lending decisions (action_taken IN 1, 2, 3, 7)
Select 16 relevant columns, drop nulls on key features
844k rows → 602k rows

[3. FEATURE ENGINEERING — 02_features.sql]
Engineer binary target variable (is_denied)
Create loan-to-income ratio, income bands, age bands

[4. JOIN — 03_join_fred.sql]
Join state-level annual average unemployment and HPI
Join national annual average mortgage rate
Final table: hmda_final (602k rows, 27 columns)

[5. MODEL — model.py]
Logistic regression on ~413k training rows
StandardScaler for feature normalization
Export predictions and feature importance for Tableau
```

---

## Data Sources

- **HMDA Data (2024):** [CFPB HMDA Data Browser](https://ffiec.cfpb.gov/data-browser/) — Home Mortgage Disclosure Act loan-level records for NC and VA
- **FRED API:** [Federal Reserve Economic Data](https://fred.stlouisfed.org/) — NCUR, VAUR (state unemployment), NCSTHPI, VASTHPI (state HPI), MORTGAGE30US (national 30-year fixed rate)

---

## Data Dictionary

### Loan Purpose Codes
| Code | Meaning |
|---|---|
| 1 | Home Purchase |
| 2 | Home Improvement |
| 31 | Refinancing |
| 32 | Cash-out Refinancing |
| 4 | Other |
| 5 | Not Applicable |

### Loan Type Codes
| Code | Meaning |
|---|---|
| 1 | Conventional |
| 2 | FHA-insured |
| 3 | VA-guaranteed |
| 4 | USDA/Rural Housing |

### Action Taken Codes (Target Variable)
| Code | Meaning | Model Label |
|---|---|---|
| 1 | Loan originated | 0 (Approved) |
| 2 | Approved, not accepted | 0 (Approved) |
| 3 | Application denied | 1 (Denied) |
| 7 | Preapproval request denied | 1 (Denied) |
| 4, 5, 6, 8 | Withdrawn / incomplete / purchased / preapproval approved | Excluded |

---

## Model Performance

| Metric | Value |
|---|---|
| ROC-AUC | 0.719 |
| Denied Recall | 0.79 |
| Denied Precision | 0.33 |
| Training Rows | ~413k |
| Test Rows | ~103k |

**Methodology:** Logistic regression with `class_weight='balanced'` to address class imbalance (approximately 80% approved, 20% denied after cleaning). Features scaled with StandardScaler prior to training.

**Feature set:** Loan amount, loan-to-value ratio, income, applicant age, loan type, loan purpose, lien status, state code, state unemployment rate, state house price index, national mortgage rate.

**Notable analytical decisions:**

- `interest_rate` excluded — structurally missing for all denied loans (banks do not assign rates to denied applications), making it a source of data leakage
- `debt_to_income_ratio` and `property_value` excluded — 25% null rate in denied loans, likely because lenders deny some applications before completing full underwriting; future iterations will incorporate missingness indicators to preserve these features rather than dropping rows
- `loan_to_income_ratio` and `dti_ltv_risk` excluded — engineered features derived from sparse inputs, dropped to avoid null propagation
- `county_code` excluded — hundreds of unique values across NC and VA would produce an unwieldy one-hot encoded feature space
- `income_band`, `loan_amount_band`, `applicant_age_band` excluded — categorical versions of numeric features already present in the model; redundant
- `state` excluded — redundant with `state_code`
- `derived_race`, `derived_sex`, `derived_ethnicity` retained for post-model fair lending analysis only — explicitly excluded as model features; the model was trained on financial factors only

---

## Limitations & Future Work

- **Sparse underwriting fields:** DTI ratio and property value are frequently missing for denied loans — likely because lenders deny some applications before completing full underwriting. A production model would incorporate missingness indicators as additional binary features rather than dropping these columns entirely.
- **LTV coefficient magnitude:** With DTI and property value removed, the model over-weights loan-to-value ratio (coefficient: 11.3) as a compensating predictor. The direction is correct — high LTV is the strongest predictor of denial — but the magnitude is inflated relative to a full-feature model.
- **Annual macro aggregation:** HMDA data does not include application month, so FRED indicators are joined as annual state-level averages. A richer dataset with monthly application dates would enable more granular macro-level analysis.
- **LTV-denial relationship:** Denial rates show a counterintuitive pattern at lower LTV ranges — likely driven by the composition of non-purchase loan types (home improvement, cash-out refi) that cluster at lower LTV values and face structurally higher denial rates regardless of collateral coverage. Controlling for loan purpose would likely restore the expected LTV-denial relationship.
- **Model complexity:** Logistic regression was chosen for interpretability. Future iterations would benchmark against gradient boosting (XGBoost/LightGBM) for improved predictive performance and incorporate missingness indicators for sparse underwriting fields.

---

## How to Run

```bash
# Clone the repo
git clone https://github.com/Tadongre12/hmda-lending-pipeline.git
cd hmda-lending-pipeline

# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your FRED API key
echo "FRED_API_KEY=your_key_here" > .env

# Download HMDA data
# Visit https://ffiec.cfpb.gov/data-browser/data/2024?category=states
# Select NC and VA, download LAR CSV to data/raw/hmda_nc_va_2024.csv

# Run pipeline
python src/ingest.py
python src/transform.py
python src/model.py
```

---

## Repository Structure

```
hmda-lending-pipeline/
├── data/
│   ├── raw/          # HMDA CSV and FRED pulls (gitignored)
│   └── processed/    # Model outputs for Tableau
├── sql/
│   ├── 01_clean.sql
│   ├── 02_features.sql
│   └── 03_join_fred.sql
├── src/
│   ├── ingest.py
│   ├── transform.py
│   └── model.py
├── dashboard/
│   └── hmda_dashboard.twbx
└── README.md
```
