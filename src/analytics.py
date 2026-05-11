import pandas as pd

def calculate_advanced_metrics(df):
    # 1. Monthly MoM Growth
    monthly_totals = df.groupby('month')['amount'].sum().reset_index()
    monthly_totals['mom_growth'] = monthly_totals['amount'].pct_change() * 100
    
    # 2. Category Contribution (%)
    total_spent = df['amount'].sum()
    category_share = df.groupby('category')['amount'].sum() / total_spent * 100
    
    # 3. Weekend vs Weekday Avg
    weekend_avg = df.groupby('is_weekend')['amount'].mean()
    
    return {
        "growth": monthly_totals,
        "share": category_share.to_dict(),
        "weekend_factor": weekend_avg.to_dict()
    }
#Anomaly Detection
def detect_spending_anomalies(df):
    anomalies_list = []
    
    # We detect anomalies per category for better accuracy
    for category in df['category'].unique():
        cat_data = df[df['category'] == category]['amount']
        
        if len(cat_data) > 5:  # Need enough data points to be statistically valid
            Q1 = cat_data.quantile(0.25)
            Q3 = cat_data.quantile(0.75)
            IQR = Q3 - Q1
            
            # Define bounds (standard multiplier is 1.5)
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Identify rows outside these bounds
            outliers = df[(df['category'] == category) & (df['amount'] > upper_bound)]
            
            for _, row in outliers.iterrows():
                anomalies_list.append({
                    "date": row['date'].strftime('%d-%m-%Y'),
                    "amount": row['amount'],
                    "category": row['category'],
                    "description": row['description']
                })
                
    return anomalies_list
#Calculating Financial health score
def calculate_financial_health_score(metrics, monthly_income, anomalies):
    # 1. Savings Rate Score (Target: 20%+)
    total_spent = sum(metrics['share'].values())
    savings_rate = max(0, (monthly_income - total_spent) / monthly_income)
    savings_score = min(100, (savings_rate / 0.20) * 100)
    
    # 2. Stability Score (Deduct points for anomalies)
    # More anomalies = lower stability
    stability_score = max(0, 100 - (len(anomalies) * 10))
    
    # 3. Essential Ratio Score (Target: Essentials < 50%)
    # We'll assume 'Rent' and 'Bills' are essentials for this logic
    essential_spend = metrics['share'].get('Rent', 0) + metrics['share'].get('Bills', 0)
    essential_ratio = essential_spend / total_spent if total_spent > 0 else 0
    essential_score = 100 if essential_ratio <= 0.50 else max(0, 100 - (essential_ratio - 0.50) * 200)
    
    # Final Weighted Calculation
    final_score = (0.4 * savings_score) + (0.3 * stability_score) + (0.3 * essential_score)
    
    # Define Label
    if final_score > 80: label = "Excellent"
    elif final_score > 60: label = "Good"
    else: label = "Needs Attention"
    
    return round(final_score, 1), label

def get_monthly_summary(df):
    """
    Bridge function to provide simple totals for the dashboard metrics.
    """
    total_spent = df['amount'].sum()
    total_income = df['income'].iloc[0] if not df.empty else 0
    savings = total_income - total_spent
    
    # Calculate advanced metrics for the health score
    adv_metrics = calculate_advanced_metrics(df)
    # We'll pass empty anomalies for now just to get the score running
    health_score, label = calculate_financial_health_score(adv_metrics, total_income, [])
    
    return {
        "total_spent": total_spent,
        "total_income": total_income,
        "savings": savings,
        "health_score": health_score,
        "health_label": label
    }