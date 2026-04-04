"""
fix_and_import.py
Step 1: Fix remaining homepage-only URLs with targeted searches
Step 2: Overwrite original CSV
Step 3: Import product_url into Supabase product_models table
"""

import csv
import time
import urllib.parse
import urllib.request
import re
import json
import os

# ─── Config ───────────────────────────────────────────────────────────────────
FILLED_FILE   = "baby_products_catalog_with_urls_FILLED.csv"
ORIGINAL_FILE = "baby_products_catalog_with_urls.csv"

SUPABASE_URL  = "https://mbyrgbtdpefncusxqzoc.supabase.co"
SUPABASE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc"

# URLs that are just homepages — we'll try to find better ones
# (brand_homepage → should be a specific product page)
HOMEPAGE_ONLY_PATTERNS = [
    "https://www.bugaboo.com/",
    "https://www.bugaboo-distributor.co.il/",
    "https://cybexonline.co.il/",
    "https://anexbaby.com/il-he/",
    "https://www.shilav.co.il/",
    "https://chiccoisrael.co.il/",
    "https://nunababy.com/usa/",
    "https://nunababy.com/en/",
    "https://nunababy.com/",
    "https://dreamonme.com/",
    "https://www.deltachildren.com/",
    "https://www.gracobaby.com/",
    "https://www.graco.com/",
    "https://www.storkcraft.com/",
    "https://www.stokke.com/",
    "https://uppababy.com/",
    "https://sport-line.co.il/",
    "https://abbottstore.com/",
]

def is_homepage_only(url):
    if not url or not url.strip():
        return True
    url = url.strip().rstrip("/")
    for h in HOMEPAGE_ONLY_PATTERNS:
        if url.rstrip("/") == h.rstrip("/"):
            return True
    return False

def ddg_search(query, num_results=5):
    results = []
    try:
        encoded = urllib.parse.quote_plus(query)
        req_url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(req_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; BabyReadyCatalog/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        pattern = r'class="result__url"[^>]*href="([^"]+)"'
        for m in re.finditer(pattern, html):
            raw_url = m.group(1)
            if "uddg=" in raw_url:
                try:
                    inner = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query).get("uddg", [""])[0]
                    if inner:
                        raw_url = inner
                except Exception:
                    pass
            if raw_url.startswith("http"):
                results.append(raw_url)
            if len(results) >= num_results:
                break
    except Exception as e:
        print(f"  Search error: {e}")
    return results

def pick_best_url(urls, brand, model):
    model_words = [w for w in model.lower().split() if len(w) > 2]
    # Priority 1: URL contains model keywords
    for url in urls:
        url_l = url.lower()
        if sum(1 for w in model_words if w in url_l) >= max(1, len(model_words) - 1):
            return url
    # Priority 2: Brand official site
    brand_slug = brand.lower().replace(" ", "")
    for url in urls:
        if brand_slug in url.lower():
            return url
    return urls[0] if urls else ""

# ─── STEP 1: Fix remaining bad URLs ──────────────────────────────────────────
print("=" * 60)
print("STEP 1: Fixing remaining homepage-only URLs")
print("=" * 60)

rows = []
with open(FILLED_FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed = 0
for i, row in enumerate(rows):
    brand = row.get("brand", "").strip()
    model = row.get("model", "").strip()
    url   = row.get("url",   "").strip()

    if not is_homepage_only(url):
        continue  # Already good

    # Try more targeted search queries
    queries = [
        f"{brand} {model} official product page",
        f'"{brand}" "{model}" baby',
        f"{brand} {model} buy",
    ]
    found = ""
    for query in queries:
        print(f"  Searching: {brand} {model} ...")
        results = ddg_search(query)
        if results:
            candidate = pick_best_url(results, brand, model)
            if not is_homepage_only(candidate):
                found = candidate
                break
        time.sleep(0.5)

    if found:
        print(f"  → Fixed: {found[:70]}")
        row["url"] = found
        fixed += 1
    else:
        print(f"  → Still no specific URL found for {brand} {model}")
    time.sleep(0.5)

print(f"\nFixed {fixed} additional URLs.\n")

# ─── STEP 2: Overwrite original CSV ──────────────────────────────────────────
print("=" * 60)
print("STEP 2: Overwriting original CSV")
print("=" * 60)

with open(ORIGINAL_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Saved {len(rows)} rows to: {ORIGINAL_FILE}\n")

# ─── STEP 3: Import product_url to Supabase product_models ───────────────────
print("=" * 60)
print("STEP 3: Importing product URLs into Supabase")
print("=" * 60)

def supabase_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    req = urllib.request.Request(url, headers={
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def supabase_patch(table, record_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.read().decode()}")
        return e.code

# Fetch all product_models with their brand info
print("Fetching product_models from Supabase...")
try:
    models = supabase_get("product_models", "select=id,model_name,brand_id,product_url&limit=500")
    print(f"  Found {len(models)} models in Supabase.")
except Exception as e:
    print(f"  ERROR fetching models: {e}")
    models = []

# Fetch all brands to build a name lookup
print("Fetching brands from Supabase...")
try:
    brands = supabase_get("brands", "select=id,name")
    brand_by_id = {b["id"]: b["name"].lower() for b in brands}
    print(f"  Found {len(brands)} brands.")
except Exception as e:
    print(f"  ERROR fetching brands: {e}")
    brand_by_id = {}

# Build a lookup: (brand_name_lower, model_name_lower) → model record
model_lookup = {}
for m in models:
    brand_name = brand_by_id.get(m.get("brand_id"), "").lower()
    model_name = (m.get("model_name") or "").lower()
    model_lookup[(brand_name, model_name)] = m

print(f"\nMatching CSV rows to Supabase models and updating product_url...\n")
updated = 0
skipped = 0
not_found = 0

for row in rows:
    csv_brand = row.get("brand", "").strip().lower()
    csv_model = row.get("model", "").strip().lower()
    csv_url   = row.get("url", "").strip()

    if not csv_url or is_homepage_only(csv_url):
        skipped += 1
        continue  # No useful URL to import

    db_model = model_lookup.get((csv_brand, csv_model))
    if not db_model:
        # Try partial match
        for (b, m), rec in model_lookup.items():
            if b == csv_brand and (m in csv_model or csv_model in m):
                db_model = rec
                break

    if not db_model:
        print(f"  NOT FOUND in DB: {csv_brand} / {csv_model}")
        not_found += 1
        continue

    current_url = db_model.get("product_url") or ""
    if current_url and not is_homepage_only(current_url):
        # Already has a good URL, don't overwrite
        skipped += 1
        continue

    # Update Supabase
    status = supabase_patch("product_models", db_model["id"], {"product_url": csv_url})
    if status in (200, 204):
        print(f"  ✅ Updated: {csv_brand} {csv_model} → {csv_url[:60]}")
        updated += 1
    else:
        print(f"  ❌ Failed ({status}): {csv_brand} {csv_model}")

print(f"\n{'='*60}")
print(f"DONE!")
print(f"  ✅ Supabase updated: {updated} models")
print(f"  ⏭️  Skipped (already had URL or no URL): {skipped}")
print(f"  ❓ Not found in DB: {not_found}")
print(f"{'='*60}")
