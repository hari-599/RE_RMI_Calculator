import pandas as pd
import os

from .extensions import redis_client
from .recommendations_data import RECOMMENDATIONS
global_weights = {
    'G.Q1': 0.0196,
    'G.Q2': 0.0062,
    'G.Q3': 0.0125,
    'G.Q4': 0.0165,
    'G.Q5': 0.0181,
    'G.Q6': 0.0080,
    'G.Q7': 0.0080,
    'G.Q8': 0.0173,
    'G.Q9': 0.0019,
    'G.Q10': 0.0037,
    'G.Q11': 0.0019,
    'G.Q12': 0.0037,
    'G.Q13': 0.0019,
    'G.Q14': 0.0037,
    'G.Q15': 0.0150,
    'G.Q16': 0.0061,
    'G.Q17': 0.0061,
    'G.Q18': 0.0061,
    'G.Q19': 0.0041,
    'G.Q20': 0.0041,
    'G.Q21': 0.0041,
    'G.Q22': 0.0041,
    'G.Q23': 0.0217,
    'G.Q24': 0.0208,
    'G.Q25': 0.0204,
    'G.Q26': 0.0225,
    'M.Q1': 0.0479,
    'M.Q2': 0.0144,
    'M.Q3': 0.0144,
    'M.Q4': 0.0144,
    'M.Q5': 0.0072,
    'M.Q6': 0.0177,
    'M.Q7': 0.0176,
    'M.Q8': 0.0176,
    'M.Q9': 0.0060,
    'M.Q10': 0.0060,
    'M.Q11': 0.0060,
    'M.Q12': 0.0060,
    'M.Q13': 0.0060,
    'M.Q14': 0.0060,
    'M.Q15': 0.0060,
    'M.Q16': 0.0060,
    'M.Q17': 0.0133,
    'M.Q18': 0.0133,
    'M.Q19': 0.0133,
    'M.Q20': 0.0133,
    'C.Q1': 0.0231,
    'C.Q2': 0.0116,
    'C.Q3': 0.0077,
    'C.Q4': 0.0487,
    'C.Q5': 0.0461,
    'C.Q6': 0.0501,
    'C.Q7': 0.0099,
    'C.Q8': 0.0112,
    'C.Q9': 0.0103,
    'C.Q10': 0.0095,
    'C.Q11': 0.0097,
    'C.Q12': 0.0105,
    'C.Q13': 0.0025,
    'C.Q14': 0.0025,
    'C.Q15': 0.0025,
    'C.Q16': 0.0025,
    'C.Q17': 0.0066,
    'C.Q18': 0.0033,
    'C.Q19': 0.0189,
    'C.Q20': 0.0168,
    'C.Q21': 0.0166,
    'C.Q22': 0.0168,
    'C.Q23': 0.0175,
    'C.Q24': 0.0159,
    'C.Q25': 0.0171,
    'C.Q26': 0.0149,
    'C.Q27': 0.0169,
    'C.Q28': 0.0083,
    'C.Q29': 0.0083
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
    print(f"File exists: {os.path.exists(file_path)}, size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'}")

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
            print(f"  Columns found: {list(df.columns)}")
            print(f"  Total rows: {len(df)}")
        except Exception as e:
            print(f"  Error reading sheet '{sheet}': {e}")
            continue
        resp_col = response_columns[sheet]
        if resp_col not in df.columns:
            print(f"WARNING: Response column '{resp_col}' not found in {sheet}")
            print(f"Available columns: {list(df.columns)}")
            print(f"  Columns found: {list(df.columns)}")
            print(f"  Total rows: {len(df)}")
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
                weight = float(global_weights.get(qn_no, 1.0))
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
            print(f"  Writing to Redis key: {redis_key}")
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
                    # try:
                    #     q_num=int(qn_no.split('Q')[1])
                    #     if q_num>=7:
                    #         consumer_cum_sum += cumulative_value
                    #         consumer_weight_sum += weight
                    # except (IndexError, ValueError):
                    #     pass
                        
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
