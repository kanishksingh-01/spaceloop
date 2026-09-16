"""
SpaceLoop Dynamic Micro-Pricing & Passive Revenue Calculator
Implements SqFt Polynomial Multiplier Model and Yield Projections.
"""

from typing import Dict, Any


CATEGORY_BASE_RATES = {
    'Workspace': 45.0,
    'Studio': 65.0,
    'Storage': 35.0,
    'Pop-up': 95.0,
    'Retail': 95.0,
    'Event': 85.0,
    'Parking': 25.0
}


def calculate_dynamic_rate(category: str, sqft: float) -> Dict[str, Any]:
    """Computes hourly and daily pricing baseline using Non-Linear SqFt Scaling.
    Formula:
      sqft_adj = max(0.8, min(2.5, sqft / 250.0))
      Rate = Base * (0.6 + 0.4 * sqft_adj)
    """
    matched_base = CATEGORY_BASE_RATES.get(category, 45.0)
    safe_sqft = max(30.0, min(25000.0, float(sqft)))
    
    sqft_adj = max(0.8, min(2.5, safe_sqft / 250.0))
    calculated_hourly = matched_base * (0.6 + (0.4 * sqft_adj))
    hourly_rate = round(calculated_hourly)
    daily_rate = round(hourly_rate * 7.5)

    return {
        'category': category,
        'sqft': safe_sqft,
        'sqft_adj': round(sqft_adj, 3),
        'base_rate': matched_base,
        'calculated_hourly': hourly_rate,
        'calculated_daily': daily_rate
    }


def calculate_host_monthly_yield(hourly_rate: float,
                                 occupancy_days_per_month: int = 12,
                                 hours_per_day: float = 6.0,
                                 platform_fee_pct: float = 0.15) -> Dict[str, Any]:
    """Calculates projected monthly net income for hosts based on realistic occupancy.
    Standard: 12 days/month @ 6 hrs/day, 15% platform take-rate.
    """
    safe_rate = max(10.0, float(hourly_rate))
    safe_days = max(1, min(31, int(occupancy_days_per_month)))
    safe_hours = max(1.0, min(24.0, float(hours_per_day)))

    monthly_hours = safe_days * safe_hours
    gross_monthly = monthly_hours * safe_rate
    platform_take = gross_monthly * platform_fee_pct
    net_monthly_income = gross_monthly - platform_take
    annual_projection = net_monthly_income * 12.0

    return {
        'hourly_rate': safe_rate,
        'occupancy_days': safe_days,
        'hours_per_day': safe_hours,
        'monthly_billable_hours': round(monthly_hours, 1),
        'gross_monthly_inr': round(gross_monthly),
        'platform_fee_inr': round(platform_take),
        'net_monthly_income_inr': round(net_monthly_income),
        'annual_projected_inr': round(annual_projection)
    }


def calculate_student_savings(hours_needed: float = 3.0, space_hourly_rate: float = 45.0) -> Dict[str, Any]:
    """Compares SpaceLoop pay-per-hour micro-rental vs commercial coworking day passes.
    Traditional coworking pass in metro India: Rs. 500 / day.
    """
    spaceloop_cost = hours_needed * space_hourly_rate
    commercial_day_pass = 550.0  # Average WeWork/Awfis/Innov8 day pass in Hauz Khas/Koramangala/Powai
    savings_inr = max(0.0, commercial_day_pass - spaceloop_cost)
    savings_pct = round((savings_inr / commercial_day_pass) * 100, 1) if commercial_day_pass > 0 else 0

    return {
        'hours_needed': hours_needed,
        'spaceloop_cost_inr': round(spaceloop_cost),
        'commercial_pass_inr': round(commercial_day_pass),
        'savings_inr': round(savings_inr),
        'savings_percentage': savings_pct
    }
