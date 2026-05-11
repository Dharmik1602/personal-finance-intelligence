def generate_quantified_recommendations(metrics, monthly_income):
    # 1. Define specific limits for the 'Early Career Professional' profile
    LIMITS = {
        'Food': 0.25,        # 25% of income
        'Shopping': 0.15,    # 15% of income
        'Travel': 0.10,      # 10% of income
        'Entertainment': 0.05 # 5% of income
    }
    
    recommendations = []
    
    for category, limit_pct in LIMITS.items():
        # Calculate actual spend for this category from the metrics
        actual_spend = metrics['share'].get(category, 0) * (sum(metrics['share'].values()) / 100)
        target_limit = monthly_income * limit_pct
        
        if actual_spend > target_limit:
            excess = actual_spend - target_limit
            savings_impact = (excess / monthly_income) * 100
            
            recommendations.append(
                f"🚨 **{category} Alert:** You are ₹{excess:.0f} over your target limit. "
                f"Reducing this could increase your monthly savings rate by {savings_impact:.1f}%."
            )
            
    if not recommendations:
        recommendations.append("✅ Great job! All your major categories are within their target limits.")
        
    return recommendations



