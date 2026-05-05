# Update this part in your Generate_dataset.py
import pandas as pd
import random
from datetime import datetime, timedelta

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
df.to_csv('data/raw/personal_expenses.csv', index=False)