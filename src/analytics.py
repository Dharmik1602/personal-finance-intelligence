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

def get_monthly_summary(df, monthly_income_override=None, savings_goal_pct=20.0):
    """
    Final bridge function that gathers ALL metrics for the dashboard.
    """
    if df is None or df.empty:
        total_spent = 0.0
        total_income = float(monthly_income_override or 0)
        savings = total_income
        return {
            "total_spent": total_spent,
            "total_income": total_income,
            "savings": savings,
            "health_score": 0.0,
            "health_label": "Needs Attention",
            "category_shares": {},
            "growth": pd.DataFrame(),
            "weekend_factor": {},
            "target_savings": total_income * (savings_goal_pct / 100),
            "savings_gap": savings - (total_income * (savings_goal_pct / 100)),
            "savings_rate": 0.0,
            "goal_progress_pct": 0.0
        }

    total_spent = float(df['amount'].sum())
    base_income = float(df['income'].iloc[0]) if 'income' in df.columns else 0.0
    total_income = float(monthly_income_override) if monthly_income_override is not None else base_income
    savings = total_income - total_spent
    
    # 1. Get ALL advanced metrics (growth, share, weekend_factor)
    adv_metrics = calculate_advanced_metrics(df)
    
    # 2. Calculate the health score
    health_score, label = calculate_financial_health_score(adv_metrics, total_income, [])

    target_savings = total_income * (savings_goal_pct / 100)
    savings_gap = savings - target_savings
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0
    goal_progress_pct = (savings / target_savings * 100) if target_savings > 0 else 0.0
    
    # 3. Return a unified dictionary with everything the dashboard needs
    return {
        "total_spent": total_spent,
        "total_income": total_income,
        "savings": savings,
        "health_score": health_score,
        "health_label": label,
        "category_shares": adv_metrics['share'],
        "growth": adv_metrics['growth'],          # FIXED: Required for insights
        "weekend_factor": adv_metrics['weekend_factor'], # FIXED: Required for insights
        "target_savings": target_savings,
        "savings_gap": savings_gap,
        "savings_rate": savings_rate,
        "goal_progress_pct": goal_progress_pct
    }