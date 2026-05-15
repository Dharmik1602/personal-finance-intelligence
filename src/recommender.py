def get_recommendations(metrics):
    """
    Standardized bridge function that evaluates monthly metrics 
    and returns quantified, actionable advice for the dashboard.
    """
    recommendations = []
    
    # 1. Extract core data from the metrics dictionary
    income = metrics.get('total_income', 0)
    category_shares = metrics.get('category_shares', {}) # Values in % (e.g., 25.5)
    total_spent = metrics.get('total_spent', 0)
    savings_gap = metrics.get('savings_gap', 0)
    target_savings = metrics.get('target_savings', 0)
    current_savings = metrics.get('savings', 0)
    
    # 2. Define specific limits for the 'Early Career Professional' profile
    LIMITS = {
        'Food': 0.25,        # 25% of income
        'Shopping': 0.15,    # 15% of income
        'Travel': 0.10,      # 10% of income
        'Entertainment': 0.05 # 5% of income
    }
    
    # 3. Category Over-Limit Analysis with Quantified Impact
    reduction_opportunities = []
    for category, limit_pct in LIMITS.items():
        # Get actual spend in INR for this category
        # Logic: (Category % of total expenses / 100) * total expenses
        cat_share_pct = category_shares.get(category, 0)
        actual_cat_spend = (cat_share_pct / 100) * total_spent
        
        target_limit_inr = income * limit_pct
        
        if actual_cat_spend > target_limit_inr:
            excess = actual_cat_spend - target_limit_inr
            savings_impact = (excess / income * 100) if income > 0 else 0
            reduction_opportunities.append((category, excess))
            
            recommendations.append(
                f"🚨 **{category} Alert:** You are ₹{excess:,.0f} over your target limit. "
                f"Reducing this could increase your monthly savings rate by {savings_impact:.1f}%."
            )

    # 4. Explicit goal-gap recommendations
    if target_savings > 0:
        if savings_gap < 0:
            required_cut = abs(savings_gap)
            recommendations.insert(
                0,
                f"🎯 **Goal Gap:** You need to free up ₹{required_cut:,.0f} this month "
                f"to reach your target savings of ₹{target_savings:,.0f} "
                f"(currently at ₹{current_savings:,.0f})."
            )

            if reduction_opportunities:
                top_category, top_excess = max(reduction_opportunities, key=lambda item: item[1])
                covered_pct = (top_excess / required_cut * 100) if required_cut > 0 else 0
                recommendations.append(
                    f"🔧 **Best Lever:** Start with **{top_category}**. "
                    f"Bringing it back to target can recover ₹{top_excess:,.0f} "
                    f"({covered_pct:.1f}% of your goal gap)."
                )
            else:
                recommendations.append(
                    "💡 No major category is over its benchmark. "
                    "Use micro-cuts across daily discretionary spending to close the remaining goal gap."
                )
        else:
            recommendations.insert(
                0,
                f"✅ **Goal On Track:** You are ₹{savings_gap:,.0f} above your target savings. "
                "Maintain current spending behavior."
            )

    # 5. Final Safety Check
    if not recommendations:
        recommendations.append("✅ Great job! All your major categories are within their target limits.")
        
    return recommendations