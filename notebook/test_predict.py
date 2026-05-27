import requests

url = "http://127.0.0.1:8001/api/predict"
payload = {
    "no_of_dependents": 2,
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 9600000.0,
    "loan_amount": 29900000.0,
    "loan_term": 12,
    "cibil_score": 778,
    "residential_assets_value": 2400000.0,
    "commercial_assets_value": 17600000.0,
    "luxury_assets_value": 22700000.0,
    "bank_asset_value": 8000000.0
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
