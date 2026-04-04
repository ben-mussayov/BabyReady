"""
insert_missing_products.py
Inserts all products from the CSV that are NOT yet in the Supabase product_models table.
Maps CSV categories (Hebrew) to existing Supabase category IDs.
"""

import csv
import json
import urllib.request
import urllib.error
import urllib.parse
import time

# ─── Config ───────────────────────────────────────────────────────────────────
CSV_FILE     = "baby_products_catalog_with_urls.csv"
SUPABASE_URL = "https://mbyrgbtdpefncusxqzoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc"

# Hebrew category name → Supabase category ID mapping
# These must match the actual IDs in the 'categories' table
HEB_TO_CAT = {
    "עגלות":          "stroller",
    "כיסאות בטיחות": "car-seat",
    "לולים ועריסות":  "crib",
    "כיסאות אוכל":   "high-chair",
    "שידות והחתלה":  "dresser",
}

# ─── HTTP helpers ──────────────────────────────────────────────────────────────
def sb_get(path, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{path}?{params}"
    req = urllib.request.Request(url, headers={
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def sb_post(path, data):
    url  = f"{SUPABASE_URL}/rest/v1/{path}"
    body = json.dumps(data).encode()
    req  = urllib.request.Request(url, data=body, headers={
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()

# ─── Fetch existing data ───────────────────────────────────────────────────────
print("Fetching existing brands, categories, and models from Supabase...")
brands_list  = sb_get("brands",         "select=id,name&limit=500")
cats_list    = sb_get("categories",     "select=id,name_he&limit=100")
models_list  = sb_get("product_models", "select=id,model_name,brand_id&limit=1000")

brand_by_name   = {b["name"].lower(): b["id"] for b in brands_list}
cat_by_id_check = {c["id"] for c in cats_list}

# Build lookup: (brand_id, model_name_lower) → True
existing = set()
for m in models_list:
    existing.add((m["brand_id"], m["model_name"].lower()))

print(f"  Brands: {len(brand_by_name)}, Models: {len(existing)}\n")

# ─── Read CSV ─────────────────────────────────────────────────────────────────
rows = []
with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

inserted = 0
skipped  = 0
errors   = 0

for row in rows:
    csv_brand   = row.get("brand",       "").strip()
    csv_model   = row.get("model",       "").strip()
    csv_desc    = row.get("description", "").strip()
    csv_url     = row.get("url",         "").strip()
    csv_cat_he  = row.get("category",   "").strip()

    if not csv_brand or not csv_model:
        skipped += 1
        continue

    # Map category
    cat_id = HEB_TO_CAT.get(csv_cat_he)
    if not cat_id or cat_id not in cat_by_id_check:
        print(f"  ⚠️  Unknown category '{csv_cat_he}' for {csv_brand} {csv_model} — skipping")
        skipped += 1
        continue

    # Ensure brand exists (get or create)
    brand_key = csv_brand.lower()
    if brand_key not in brand_by_name:
        print(f"  Creating brand: {csv_brand}")
        new_brand, err = sb_post("brands", {"name": csv_brand})
        if err or not new_brand:
            print(f"  ❌ Failed to create brand {csv_brand}: {err}")
            errors += 1
            continue
        brand_id = new_brand[0]["id"]
        brand_by_name[brand_key] = brand_id
        time.sleep(0.2)
    else:
        brand_id = brand_by_name[brand_key]

    # Check if model already exists
    if (brand_id, csv_model.lower()) in existing:
        skipped += 1
        continue

    # Insert new product model
    payload = {
        "category_id": cat_id,
        "brand_id":    brand_id,
        "model_name":  csv_model,
        "description": csv_desc or None,
        "product_url": csv_url  or None,
        "active":      True,
    }

    result, err = sb_post("product_models", payload)
    if err:
        print(f"  ❌ Error inserting {csv_brand} {csv_model}: {err[:100]}")
        errors += 1
    else:
        model_id = result[0]["id"]
        existing.add((brand_id, csv_model.lower()))
        print(f"  ✅ Inserted: {csv_brand} {csv_model}")
        inserted += 1

    time.sleep(0.1)

print(f"\n{'='*60}")
print(f"DONE!")
print(f"  ✅ Inserted: {inserted} new product models")
print(f"  ⏭️  Skipped (already existed): {skipped}")
print(f"  ❌ Errors: {errors}")
print(f"{'='*60}")
