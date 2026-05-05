import pandas as pd
import os

def clean_and_feature_engineer(input_path, output_path):
    df = pd.read_csv(input_path)
    df.columns = [col.lower() for col in df.columns]
    
    # 1. Date Fix (the root of the first error)
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    
    # 2. Amount & Income as Floats
    for col in ['amount', 'income']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 3. Module 4: Feature Engineering
    df['month'] = df['date'].dt.month_name()
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_weekend'] = df['date'].dt.weekday >= 5 
    
    # Burn Rate: Cumulative spending
    df = df.sort_values('date')
    df['cumulative_spent'] = df.groupby('month')['amount'].cumsum()
    
    # Savings Feature: (Monthly Income - Cumulative Spent)
    # This is only possible with the separate income column!
    df['remaining_budget'] = df['income'] - df['cumulative_spent']

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Root fix applied! Processed data saved with 'income' column.")

if __name__ == "__main__":
    clean_and_feature_engineer('data/raw/personal_expenses.csv', 'data/processed/cleaned_expenses.csv')