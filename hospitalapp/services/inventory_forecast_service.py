import math
import datetime
from hospitalapp.models import Vaccinetbl, Hospitaltbl
from patientapp.models import Appointmenttbl


def generate_inventory_forecast_for_hospital(hospital_id: int, forecast_days: int = 14) -> list:
    """
    Generates predictive inventory forecasts for all vaccines in a hospital's catalogue.
    Forecast period defaults to 14 days (supports 7, 14, or 30 days).
    
    Returns a list of dicts:
    [
        {
            'vaccine_id': v.id,
            'vaccine_name': v.vaccineName,
            'stock_quantity': v.stock_quantity,
            'minimum_quantity': v.minimum_quantity,
            'forecast_days': forecast_days,
            'upcoming_booked_demand': 12,
            'projected_usage_demand': 4,
            'total_expected_demand': 16,
            'projected_remaining_stock': -8,
            'risk_level': 'CRITICAL' | 'AT_RISK' | 'MONITOR' | 'SAFE',
            'recommended_restock': 13,
            'explanations': ['Explanation 1', 'Explanation 2']
        },
        ...
    ]
    """
    try:
        hospital = Hospitaltbl.objects.get(pk=hospital_id)
    except Hospitaltbl.DoesNotExist:
        return []

    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=forecast_days)
    past_30_days = today - datetime.timedelta(days=30)

    vaccines = Vaccinetbl.objects.filter(hospitalId=hospital).order_by('vaccineName')
    forecasts = []

    for v in vaccines:
        # 1. Upcoming booked appointment demand in next N days
        upcoming_apts_count = Appointmenttbl.objects.filter(
            hospitalid=hospital,
            vaccineid=v,
            aptdate__gte=today,
            aptdate__lte=future_date
        ).exclude(active=3).count() # exclude cancelled

        # 2. Historical usage over past 30 days (completed appointments)
        historical_completed_count = Appointmenttbl.objects.filter(
            hospitalid=hospital,
            vaccineid=v,
            aptdate__gte=past_30_days,
            aptdate__lt=today,
            active=2 # completed
        ).count()

        daily_historical_rate = historical_completed_count / 30.0
        projected_historical_demand = math.ceil(daily_historical_rate * forecast_days)

        total_expected_demand = upcoming_apts_count + projected_historical_demand
        projected_remaining = v.stock_quantity - total_expected_demand

        # 3. Classify Risk Level
        explanations = []
        if v.stock_quantity <= 0:
            risk_level = 'CRITICAL'
            explanations.append("Current stock is 0 doses (Out of Stock).")
        elif v.stock_quantity < upcoming_apts_count:
            risk_level = 'CRITICAL'
            explanations.append(f"Current stock ({v.stock_quantity}) is insufficient for confirmed upcoming bookings ({upcoming_apts_count} appointments).")
        elif projected_remaining < 0:
            risk_level = 'AT_RISK'
            explanations.append(f"Projected demand ({total_expected_demand} doses) exceeds current stock ({v.stock_quantity} doses).")
        elif projected_remaining < v.minimum_quantity:
            risk_level = 'MONITOR'
            explanations.append(f"Projected remaining stock ({projected_remaining} doses) approaches minimum threshold ({v.minimum_quantity} doses).")
        else:
            risk_level = 'SAFE'
            explanations.append("Stock comfortably covers projected upcoming demand and threshold.")

        # 4. Recommended Restock Quantity
        if risk_level in ['AT_RISK', 'CRITICAL', 'MONITOR']:
            needed = total_expected_demand - v.stock_quantity + v.minimum_quantity
            recommended_restock = max(0, needed)
        else:
            recommended_restock = 0

        # Detailed breakdown explanation
        explanations.append(f"• {upcoming_apts_count} confirmed/scheduled appointments in next {forecast_days} days.")
        explanations.append(f"• {projected_historical_demand} estimated demand based on recent usage rate ({historical_completed_count} doses in last 30 days).")

        forecasts.append({
            'vaccine_id': v.id,
            'vaccine_name': v.vaccineName,
            'stock_quantity': v.stock_quantity,
            'minimum_quantity': v.minimum_quantity,
            'price': v.price,
            'forecast_days': forecast_days,
            'upcoming_booked_demand': upcoming_apts_count,
            'projected_usage_demand': projected_historical_demand,
            'total_expected_demand': total_expected_demand,
            'projected_remaining_stock': projected_remaining,
            'risk_level': risk_level,
            'recommended_restock': recommended_restock,
            'explanations': explanations
        })

    return forecasts
