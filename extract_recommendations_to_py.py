import pandas as pd

# Path to your Excel file
EXCEL_PATH = 'static/General recommendations.xlsx'
# Output Python file
OUTPUT_PATH = 'recommendations_data.py'

# Read all sheets and collect recommendations
xl = pd.ExcelFile(EXCEL_PATH)
recommendations = {}
for sheet_name in xl.sheet_names:
    df = xl.parse(sheet_name, header=2)
    print(df.columns)
    for _, row in df.iterrows():
        qn = str(row.get('Question no.')).strip()
        rec = row.get('Recommendations') or row.get('General Recommendation')
        if qn and rec:
            recommendations[qn] = str(rec).strip()

# Write to Python file
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('# Auto-generated from General recommendations.xlsx\n')
    f.write('RECOMMENDATIONS = ')
    f.write(repr(recommendations))

print(f"Extracted {len(recommendations)} recommendations to {OUTPUT_PATH}")
