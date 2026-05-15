# Personal Finance Intelligence: Product Layer Rules

You are an expert Python and Streamlit developer. Your goal is to transform this analytical backend into a high-end, interactive Financial Intelligence Product.

## 🏗️ Project Architecture
- **Frontend**: Streamlit (`app/main.py`)
- **Backend Logic**: Data processing (`src/processor.py`), Analytics (`src/analytics.py`), Coaching (`src/insights.py`, `src/recommender.py`)
- **Data Persistence**: All user inputs and logs must eventually update `data/raw/personal_expenses.csv`.

## 🛠️ Feature Requirements

### 1. Dynamic User Inputs (Sidebar)
- Implement `st.sidebar.number_input` for **Monthly Salary** and **Savings Goal %**.
- These inputs must override any static values in the CSV and globally affect the `summary` dictionary.
- Calculate a "Target Savings INR" based on (Salary * Goal %) to show as a secondary KPI.

### 2. Transaction Logging (Data Entry)
- Build a transaction logger using `st.sidebar.form` or a dedicated `st.expander`.
- Required fields: Date, Amount (INR), Category (Dropdown), and Description.
- On submit: 
    1. Append the row to `data/raw/personal_expenses.csv`.
    2. Trigger `clean_and_feature_engineer()` to refresh the processed data.
    3. Call `st.rerun()` to update all charts and the Coach instantly.

### 3. UI/UX & Visual Standards
- **Theme**: Force a professional Dark Mode aesthetic.
- **Plotly Fixes**: 
    - Always use `template="plotly_dark"`.
    - Explicitly set `hoverlabel=dict(bgcolor="black", font_size=14, font_color="white")` to ensure tags are readable against dark backgrounds.
    - Use `width="stretch"` for all `st.plotly_chart` calls.
- **KPI Styling**: Use `st.metric` with `delta` indicators to show how close the user is to their savings goal.

## 🧠 Logical Constraints
- **Bridge Functions**: Never perform heavy math in `main.py`. Always call the bridge functions in `src/`.
- **Error Handling**: Use `.get()` and `if not empty` checks to ensure the dashboard doesn't crash when a user selects a month with no data.
- **Currency**: Always format currency as `₹{value:,.0f}`.