import pandas as pd
import redis
from recommendations_data import RECOMMENDATIONS
from extensions import redis_client
global_weights = {
    'G.Q1': 0.01957749053,
    'G.Q2': 0.006231762569,
    'G.Q3': 0.01248223914,
    'G.Q4': 0.016487927,
    'G.Q5': 0.01808693852,
    'G.Q6': 0.008037266873,
    'G.Q7': 0.008037266873,
    'G.Q8': 0.01729457159,
    'G.Q9': 0.001865672155,
    'G.Q10': 0.003748152167,
    'G.Q11': 0.001865672155,
    'G.Q12': 0.00373134431,
    'G.Q13': 0.001865672155,
    'G.Q14': 0.00373134431,
    'G.Q15': 0.01501799423,
    'G.Q16': 0.00606171739,
    'G.Q17': 0.006079920745,
    'G.Q18': 0.00606171739,
    'G.Q19': 0.004084156845,
    'G.Q20': 0.004084156845,
    'G.Q21': 0.004084156845,
    'G.Q22': 0.004084156845,
    'G.Q23': 0.02166819574,
    'G.Q24': 0.02079015475,
    'G.Q25': 0.02036687681,
    'G.Q26': 0.02253165972,
    'M.Q1': 0.04789201967,
    'M.Q2': 0.01443893863,
    'M.Q3': 0.01443893863,
    'M.Q4': 0.01443893863,
    'M.Q5': 0.007168983517,
    'M.Q6': 0.01767070954,
    'M.Q7': 0.01761780323,
    'M.Q8': 0.01761780323,
    'M.Q9': 0.006039249402,
    'M.Q10': 0.006039249402,
    'M.Q11': 0.006039249402,
    'M.Q12': 0.006039249402,
    'M.Q13': 0.006039249402,
    'M.Q14': 0.006039249402,
    'M.Q15': 0.006039249402,
    'M.Q16': 0.006039249402,
    'M.Q17': 0.01326522751,
    'M.Q18': 0.01326522751,
    'M.Q19': 0.01326522751,
    'M.Q20': 0.01326522751,
    'C.Q1': 0.02308375746,
    'C.Q2': 0.01156305649,
    'C.Q3': 0.007708704327,
    'C.Q4': 0.04873863508,
    'C.Q5': 0.04607604857,
    'C.Q6': 0.05010154934,
    'C.Q7': 0.01129079994,
    'C.Q8': 0.01036887107,
    'C.Q9': 0.009647835548,
    'C.Q10': 0.009808386133,
    'C.Q11': 0.002659103595,
    'C.Q12': 0.002659103595,
    'C.Q13': 0.002659103595,
    'C.Q14': 0.002659103595,
    'C.Q15': 0.006805744972,
    'C.Q16': 0.003397770728,
    'C.Q17': 0.01454726854,
    'C.Q18': 0.01289733756,
    'C.Q19': 0.01279091063,
    'C.Q20': 0.01292354044,
    'C.Q21': 0.01345903476,
    'C.Q22': 0.01939009674,
    'C.Q23': 0.01924099275,
    'C.Q24': 0.009181640538,
    'C.Q25': 0.009181640538,
    'C.Q26': 0.01663118099,
    'C.Q27': 0.01451410295,
    'C.Q28': 0.01639318135,
    'C.Q29': 0.01621245577
}

def clear_redis_data(redis_client):
    """Clear all relevant data from Redis"""
    # Clear sheet data
    sheet_keys = redis_client.keys('sheet:*')
    if sheet_keys:
        for key in sheet_keys:
            redis_client.delete(key)
        print(f"Cleared {len(sheet_keys)} sheet keys")

    # Clear summary values
    redis_client.delete('summary_values')
    print("Cleared summary values")

    # Clear electricity data
    electricity_keys = redis_client.keys('electricity_data:user:*')
    if electricity_keys:
        for key in electricity_keys:
            redis_client.delete(key)
        print(f"Cleared {len(electricity_keys)} electricity data keys")

    # Clear weights
    redis_client.delete('global_weights')
    print("Cleared global weights")

    # Verify all data is cleared
    remaining = len(redis_client.keys('sheet:*')) + len(redis_client.keys('electricity_data:user:*'))
    if remaining > 0:
        print(f"Warning: {remaining} keys still remain")
    else:
        print("All relevant data cleared successfully")

def is_empty_or_nan(value):
    """Check if value is empty, NaN, or 'nan' string"""
    if pd.isna(value):
        return True
    if value is None:
        return True
    str_val = str(value).strip()
    if str_val == '':
        return True
    if str_val.lower() in ['nan', 'none', 'null']:
        return True
    return False

def process_excel(file_path):
    print("process_excel calledhj!", flush=True)
    print("HELLO", flush=True)

    response_columns = {
        'GOVERNANCE': 'GOV_Response Value',
        'MARKET CONDITIONS': 'MC_Response Value',
        'NON-PROSUMERS': 'NON-PROSUMERS',
        'LIVE-PROSUMERS': 'CP(LP)_Response Value',
    }
    # For summary values
    governance_cum_sum = 0.0
    governance_weight_sum = 0.0
    market_cum_sum = 0.0
    market_weight_sum = 0.0
    consumer_cum_sum = 0.0
    consumer_weight_sum = 0.0
    total_cum_sum = 0.0
    for sheet in response_columns:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, header=2)
            df.columns = df.columns.str.strip()
        except Exception as e:
            continue
        resp_col = response_columns[sheet]
        if resp_col not in df.columns:
            print(f"WARNING: Response column '{resp_col}' not found in {sheet}")
            print(f"Available columns: {list(df.columns)}")
            continue
        for idx, row in df.iterrows():
            indicator_raw = row.get('Indicator', '')
            subindicator_raw = row.get('Sub-Indicator', '')
            qn_no_raw = row.get('Question no.', '')
            response_value_raw = row.get(resp_col)
            indicator = str(indicator_raw).strip() if not is_empty_or_nan(indicator_raw) else ''
            subindicator = str(subindicator_raw).strip() if not is_empty_or_nan(subindicator_raw) else ''
            qn_no = str(qn_no_raw).strip() if not is_empty_or_nan(qn_no_raw) else ''
            if indicator.lower() == 'nan':
                indicator = ''
            if subindicator.lower() == 'nan':
                subindicator = ''
            if qn_no.lower() == 'nan':
                qn_no = ''
            if not qn_no:
                print(f"  Skipping row {idx} - no question number")
                continue
            try:
                weight = round(float(global_weights.get(qn_no, 1.0)),2)
                print(weight)
            except (ValueError, TypeError):
                weight = 1.0
            try:
                if is_empty_or_nan(response_value_raw):
                    resp_val_rounded = None
                    cumulative_value = None
                    print(f"  Response value is empty/NaN")
                else:
                    resp_val = float(response_value_raw)
                    resp_val_rounded = resp_val
                    cumulative_value = resp_val_rounded * weight
            except (TypeError, ValueError) as e:
                print(f"  Invalid response value at {sheet} -> {qn_no}: {response_value_raw} ({e})")
                resp_val_rounded = None
                cumulative_value = None
            redis_key = f"sheet:{sheet}:indicator:{indicator}:subindicator:{subindicator}:qn:{qn_no}"
            redis_data = {
                'sheet': sheet,
                'indicator': indicator,
                'subindicator': subindicator,
                'qn_no': qn_no,
                'global_weight': weight          }
            if resp_val_rounded is not None:
                redis_data['response_value'] = resp_val_rounded
            if cumulative_value is not None:
                redis_data['cumulative_value'] = cumulative_value
                total_cum_sum += cumulative_value
                if qn_no.startswith('G.'):
                    governance_cum_sum += cumulative_value
                    governance_weight_sum += weight
                elif qn_no.startswith('M.'):
                    market_cum_sum += cumulative_value
                    market_weight_sum += weight
                elif qn_no.startswith('C.'):
                    consumer_cum_sum += cumulative_value
                    consumer_weight_sum += weight
            try:
                redis_client.hset(redis_key, mapping=redis_data)
                print(f"  Successfully saved to Redis")
            except Exception as e:
                print(f"  Redis save error: {e}")
        print(total_cum_sum)
    # Save summary values to Redis
    summary_data = {
        'governance_maturity_index': round((governance_cum_sum / governance_weight_sum)*100, 1) if governance_weight_sum else 0.0,
        'market_maturity_index': round((market_cum_sum / market_weight_sum)*100, 1) if market_weight_sum else 0.0,
        'consumer_maturity_index': round((consumer_cum_sum / consumer_weight_sum)*100, 1) if consumer_weight_sum else 0.0,
        'sum_of_cum': total_cum_sum,
        'sum_of_weights': round(governance_weight_sum + market_weight_sum + consumer_weight_sum, 1)
    }
    redis_client.hset('summary_values', mapping=summary_data)

# Helper function to clear only governance data for testing
def clear_governance_data():
    keys = redis_client.keys('sheet:GOVERNANCE:*')
    for key in keys:
        redis_client.delete(key)
    print(f"Cleared {len(keys)} governance keys from Redis")

def get_20_min_response_recommendations():
    """
    Get 20 minimum response values from Redis and fetch their general recommendations from the static Python dict.
    Returns a list of dicts: [{qn_no, response_value, recommendation}]
    Avoids duplicate recommendations in the result.
    """
    all_keys = redis_client.keys('sheet:*')
    qn_responses = []
    for key in all_keys:
        data = redis_client.hgetall(key)
        qn_no = data.get('qn_no')
        resp_val = data.get('response_value')
        if qn_no and resp_val is not None:
            try:
                resp_val = float(resp_val)
                qn_responses.append({'qn_no': qn_no, 'response_value': resp_val})
            except Exception:
                continue
    qn_responses.sort(key=lambda x: x['response_value'])
    min_20 = qn_responses[:40]  # get more in case of duplicates
    seen_recs = set()
    unique_results = []
    for item in min_20:
        rec = RECOMMENDATIONS.get(item['qn_no'], 'No recommendation found')
        if rec not in seen_recs:
            item['recommendation'] = rec
            unique_results.append(item)
            seen_recs.add(rec)
        if len(unique_results) == 20:
            break
    return unique_results
