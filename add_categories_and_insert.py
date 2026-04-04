"""
add_categories_and_insert.py
1. Adds missing 'high-chair' and 'dresser' categories to Supabase
2. Re-runs the insert for the skipped products
"""

import csv, json, time, urllib.request, urllib.error

SUPABASE_URL = "https://mbyrgbtdpefncusxqzoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc"
CSV_FILE     = "baby_products_catalog_with_urls.csv"

HEB_TO_CAT = {
    "עגלות":          "stroller",
    "כיסאות בטיחות": "car-seat",
    "לולים ועריסות":  "crib",
    "כיסאות אוכל":   "high-chair",
    "שידות והחתלה":  "dresser",
}

def sb_get(path, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{path}?{params}"
    req = urllib.request.Request(url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def sb_post(path, data, upsert=False):
    url  = f"{SUPABASE_URL}/rest/v1/{path}"
    body = json.dumps(data).encode()
    prefer = "resolution=merge-duplicates,return=representation" if upsert else "return=representation"
    req  = urllib.request.Request(url, data=body, headers={
        "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json", "Prefer": prefer,
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()

# ─── STEP 1: Ensure categories exist ──────────────────────────────────────────
print("STEP 1: Ensuring all categories exist...")

NEW_CATS = [
    {"id": "high-chair", "name_en": "High Chairs",       "name_he": "כיסאות אוכל",   "icon": "🪑", "urgency": "low",    "priority": 5,  "is_essential": True},
    {"id": "dresser",    "name_en": "Dressers & Changing","name_he": "שידות והחתלה",  "icon": "🗄️", "urgency": "medium", "priority": 6,  "is_essential": True},
]
for cat in NEW_CATS:
    result, err = sb_post("categories", cat, upsert=True)
    if err:
        print(f"  ⚠️  Category {cat['id']}: {err[:80]}")
    else:
        print(f"  ✅ Category ready: {cat['id']} ({cat['name_he']})")
    time.sleep(0.2)

# Refresh categories
cats_list = sb_get("categories", "select=id,name_he&limit=100")
cat_by_id_check = {c["id"] for c in cats_list}
print(f"  Categories in DB: {sorted(cat_by_id_check)}\n")

# ─── STEP 2: Re-insert skipped products ───────────────────────────────────────
print("STEP 2: Inserting remaining products...")

brands_list  = sb_get("brands",         "select=id,name&limit=500")
models_list  = sb_get("product_models", "select=id,model_name,brand_id&limit=1000")

brand_by_name = {b["name"].lower(): b["id"] for b in brands_list}
existing = set()
for m in models_list:
    existing.add((m["brand_id"], m["model_name"].lower()))

rows = []
with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

inserted = 0
skipped  = 0
errors   = 0

for row in rows:
    csv_brand  = row.get("brand",       "").strip()
    csv_model  = row.get("model",       "").strip()
    csv_desc   = row.get("description", "").strip()
    csv_url    = row.get("url",         "").strip()
    csv_cat_he = row.get("category",    "").strip()

    if not csv_brand or not csv_model:
        skipped += 1; continue

    cat_id = HEB_TO_CAT.get(csv_cat_he)
    if not cat_id or cat_id not in cat_by_id_check:
        print(f"  ⚠️  Still unknown cat '{csv_cat_he}' — {csv_brand} {csv_model}")
        skipped += 1; continue

    brand_key = csv_brand.lower()
    if brand_key not in brand_by_name:
        new_brand, err = sb_post("brands", {"name": csv_brand})
        if err or not new_brand:
            print(f"  ❌ Brand create failed: {csv_brand}: {err}"); errors += 1; continue
        brand_id = new_brand[0]["id"]
        brand_by_name[brand_key] = brand_id
        time.sleep(0.2)
    else:
        brand_id = brand_by_name[brand_key]

    if (brand_id, csv_model.lower()) in existing:
        skipped += 1; continue

    payload = {"category_id": cat_id, "brand_id": brand_id, "model_name": csv_model,
               "description": csv_desc or None, "product_url": csv_url or None, "active": True}
    result, err = sb_post("product_models", payload)
    if err:
        print(f"  ❌ {csv_brand} {csv_model}: {err[:100]}"); errors += 1
    else:
        existing.add((brand_id, csv_model.lower()))
        print(f"  ✅ Inserted: {csv_brand} {csv_model}")
        inserted += 1
    time.sleep(0.1)

print(f"\n{'='*60}")
print(f"DONE! ✅ Inserted: {inserted} | ⏭️ Skipped: {skipped} | ❌ Errors: {errors}")
print(f"{'='*60}")
