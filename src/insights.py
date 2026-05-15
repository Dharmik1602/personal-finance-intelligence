import pandas as pd

def generate_automated_insights(metrics):
    """
    Translates raw analytical data into human-readable narratives.
    """
    insights = []

    total_income = metrics.get('total_income', 0)
    savings = metrics.get('savings', 0)
    target_savings = metrics.get('target_savings', 0)
    savings_gap = metrics.get('savings_gap', 0)
    goal_progress_pct = metrics.get('goal_progress_pct', 0)

    # 0. Goal Progress Narrative (new primary insight)
    if total_income > 0 and target_savings > 0:
        if savings_gap >= 0:
            insights.append(
                f"🎯 You are ahead of your savings goal by ₹{savings_gap:,.0f} "
                f"({goal_progress_pct:.1f}% of target achieved)."
            )
        else:
            insights.append(
                f"🎯 You are short of your savings goal by ₹{abs(savings_gap):,.0f}. "
                f"Current savings: ₹{savings:,.0f} vs target: ₹{target_savings:,.0f}."
            )
    
    # 1. Safety Check: Ensure the 'growth' data exists
    if 'growth' in metrics and not metrics['growth'].empty:
        mom_growth = metrics['growth']['mom_growth'].iloc[-1]
        if mom_growth > 0:
            insights.append(f"📈 Your spending increased by {mom_growth:.1f}% compared to last month.")
        else:
            insights.append(f"📉 Great job! Your spending decreased by {abs(mom_growth):.1f}% this month.")
        
    # 2. Category Insight (Updated to use 'category_shares')
    category_shares = metrics.get('category_shares', {})
    for cat, share in category_shares.items():
        if share > 25: 
            insights.append(f"⚠️ {cat} is your biggest expense, taking up {share:.1f}% of your budget.")
            
    # 3. Behavioral Patterns
    weekend_factor = metrics.get('weekend_factor', {})
    weekend_avg = weekend_factor.get(True, 0)
    weekday_avg = weekend_factor.get(False, 0)
    
    if weekend_avg > weekday_avg and weekday_avg > 0:
        diff = ((weekend_avg - weekday_avg) / weekday_avg) * 100
        insights.append(f"🍺 Weekend Spike: You spend {diff:.1f}% more on Saturdays and Sundays.")

    if not insights:
        insights.append("No strong signals this month yet. Keep logging transactions for richer insights.")
        
    return insights