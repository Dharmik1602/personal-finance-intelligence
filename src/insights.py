def generate_spending_insights(metrics):
    insights = []
    
    # 1. Growth Insight
    mom_growth = metrics['growth']['mom_growth'].iloc[-1]
    if mom_growth > 0:
        insights.append(f"📈 Your spending increased by {mom_growth:.1f}% compared to last month.")
    else:
        insights.append(f"📉 Great job! Your spending decreased by {abs(mom_growth):.1f}% this month.")
        
    # 2. Category Share Insight
    for cat, share in metrics['share'].items():
        if share > 25: # Threshold for 'high' spending
            insights.append(f"⚠️ {cat} is your biggest expense, taking up {share:.1f}% of your total budget.")
            
    # 3. Weekend Behavior
    weekend_avg = metrics['weekend_factor'].get(True, 0)
    weekday_avg = metrics['weekend_factor'].get(False, 0)
    
    if weekend_avg > weekday_avg:
        diff = ((weekend_avg - weekday_avg) / weekday_avg) * 100
        insights.append(f"🍺 Weekend Spike: You spend {diff:.1f}% more on Saturdays and Sundays.")
        
    return insights