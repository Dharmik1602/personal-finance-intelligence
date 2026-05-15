# Update this part in your Generate_dataset.py
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
start_date = datetime(2025, 1, 1)
num_days = 180 
salary = 60000 

data = []

for i in range(num_days):
    current_date = start_date + timedelta(days=i)
    
    # Monthly Income column logic: 
    # We assign the monthly salary to the first of the month, 
    # or keep a fixed monthly_income reference for every row.
    monthly_inc = salary if current_date.day == 1 else 0
    
    # Standard Daily Expense
    data.append([
        current_date.strftime('%d-%m-%Y'), 
        random.randint(200, 800), 
        'Food', 
        'UPI', 
        'Daily Meals', 
        salary # Every row now knows the user's monthly income context
    ])

# New Column Schema
df = pd.DataFrame(data, columns=['date', 'amount', 'category', 'payment_mode', 'description', 'income'])
# Synthetic demo for notebooks / formula checks — not the Streamlit app raw ledger.
_ROOT = Path(__file__).resolve().parents[2]
_out = _ROOT / "data" / "samples" / "personal_expenses_generated_demo.csv"
_out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(_out, index=False)