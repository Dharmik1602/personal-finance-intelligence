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
    # Use .dt.month for numeric sorting (1, 2, 3...)
    df['month'] = df['date'].dt.month 
    
    # Use .dt.month_name() for the dashboard labels (January, February...)
    df['month_name'] = df['date'].dt.month_name() 
    
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_weekend'] = df['date'].dt.weekday >= 5 
    
    # Burn Rate: Cumulative spending
    df = df.sort_values('date')
    # Group by 'month_name' so the cumulative sum resets each month
    df['cumulative_spent'] = df.groupby('month_name')['amount'].cumsum()

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Root fix applied! Processed data saved with 'income' column.")

if __name__ == "__main__":
    clean_and_feature_engineer('data/raw/personal_expenses.csv', 'data/processed/cleaned_expenses.csv')