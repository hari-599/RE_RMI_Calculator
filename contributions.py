import redis
from flask_login import current_user
import math
from extensions import redis_client

def save_or_update_electricity_data(form_data):
    generation = int(form_data['generation'])
    consumption = int(form_data['consumption'])
    percentage = (consumption / generation) * 100 if consumption else 0.0

    # Use a Redis hash per user
    redis_key = f"electricity_data:user:{current_user.id}"
    redis_client.hmset(redis_key, {
        'state': form_data['state'],
        'district': form_data['district'],
        'board_circle': form_data['board_circle'],
        'division': form_data['division'],
        'section_office': form_data['section_office'],
        'domestic_consumers': int(form_data['domestic_consumers']),
        'renewable_prosumers': int(form_data['renewable_prosumers']),
        'annual_generation': generation,
        'annual_consumption': consumption,
        'percentage_contribution': round(percentage, 1)
    })
    # Calculate and store re_rmi_value
    try:
        sum_of_cum = float(redis_client.hget('summary_values', 'sum_of_cum') or 0.0)
    except Exception:
        sum_of_cum = 0.0
    re_rmi_value = (sum_of_cum +(percentage*0.052791818))*100
    print(re_rmi_value,sum_of_cum, percentage)
    redis_client.hset(redis_key, 're_rmi_value', math.ceil(re_rmi_value))
    return round(percentage, 2)

def reset_electricity_data():
    """Delete the current user's electricity data from Redis."""
    redis_key = f"electricity_data:user:{current_user.id}"
    redis_client.delete(redis_key)
