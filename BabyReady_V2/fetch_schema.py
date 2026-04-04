import json
import requests

URL = "https://mbyrgbtdpefncusxqzoc.supabase.co/rest/v1/"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc"

openapi_url = f"{URL}?apikey={KEY}"
r = requests.get(openapi_url)

if r.status_code == 200:
    data = r.json()
    definitions = data.get("definitions", {})
    
    # We only care about user_items and product_prices and similar tables
    tables_of_interest = ["user_items", "product_prices", "profiles", "product_models", "stores"]
    
    schema_summary = {}
    for table_name in tables_of_interest:
        if table_name in definitions:
            props = definitions[table_name].get("properties", {})
            schema_summary[table_name] = {k: v.get('type', v.get('format', 'unknown')) for k, v in props.items()}
    
    print(json.dumps(schema_summary, indent=2))
else:
    print(f"Failed to fetch schema: {r.status_code} - {r.text}")
