"""
fill_urls.py - Auto-fill missing product URLs in the baby products catalog
Uses DuckDuckGo search (no API key required) to find the best product page for each item.
"""

import csv
import time
import urllib.parse
import urllib.request
import re
import json
import os

INPUT_FILE  = "baby_products_catalog_with_urls.csv"
OUTPUT_FILE = "baby_products_catalog_with_urls_FILLED.csv"

# Known brand home pages — used as fallback and for "home-page-only" detection
BRAND_HOMES = {
    "bugaboo": "https://www.bugaboo-distributor.co.il/",
    "cybex":   "https://cybexonline.co.il/",
    "anex":    "https://anexbaby.com/il-he/",
    "uppababy": "https://www.shilav.co.il/",
    "nuna":    None,  # no single IL site — will search
    "chicco":  "https://chiccoisrael.co.il/",
    "stokke":  None,
    "storkcraft": None,
    "graco":   None,
    "delta children": None,
    "dream on me": None,
    "child craft": None,
    "sport line": None,
}

def is_homepage_only(url, brand):
    """Return True if url is just the brand homepage (not a specific product page)."""
    if not url or not url.strip():
        return True
    url = url.strip().rstrip("/")
    brand_lower = brand.lower()
    for key, home in BRAND_HOMES.items():
        if key in brand_lower and home:
            if url.rstrip("/") == home.rstrip("/"):
                return True
    return False

def ddg_search(query, num_results=5):
    """
    Search DuckDuckGo and return list of (title, url) results.
    Uses the instant-answer API (no JS / API key required).
    """
    results = []
    try:
        encoded = urllib.parse.quote_plus(query)
        # DuckDuckGo HTML search (lite version is easiest to parse)
        req_url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(req_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; BabyReadyCatalog/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract result links from DDG HTML
        pattern = r'<a[^>]+class="result__url"[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
        for m in re.finditer(pattern, html):
            raw_url = m.group(1)
            # DDG wraps links; decode the redirect
            if "uddg=" in raw_url:
                try:
                    inner = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query).get("uddg", [""])[0]
                    if inner:
                        raw_url = inner
                except Exception:
                    pass
            results.append(raw_url)
            if len(results) >= num_results:
                break
    except Exception as e:
        print(f"  Search error: {e}")
    return results

def pick_best_url(urls, brand, model):
    """Pick the most specific / relevant URL for this product."""
    brand_l = brand.lower()
    model_l  = model.lower().replace(" ", "-")
    model_words = model.lower().split()

    # Priority 1: URL contains the model name or most of its words
    for url in urls:
        url_l = url.lower()
        if model_l in url_l or all(w in url_l for w in model_words if len(w) > 2):
            return url

    # Priority 2: URL is from a known Israeli retailer / brand site
    preferred_domains = [
        "bugaboo-distributor.co.il", "cybexonline.co.il", "anexbaby.com",
        "shilav.co.il", "chiccoisrael.co.il", "aglis.co.il", "babystar.co.il",
        "motzetzim.co.il", "stokke.com/il", "graco.com", "storkcraft.com",
        brand_l.replace(" ", "")
    ]
    for domain in preferred_domains:
        for url in urls:
            if domain in url.lower():
                return url

    # Fallback: return first result
    return urls[0] if urls else ""

def main():
    rows = []
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} products. Searching for missing URLs...\n")

    changed = 0
    for i, row in enumerate(rows):
        brand  = row.get("brand",  "").strip()
        model  = row.get("model",  "").strip()
        url    = row.get("url",    "").strip()

        if not is_homepage_only(url, brand):
            # Already has a specific URL — skip
            print(f"[{i+1:3}] SKIP  {brand} {model}: already has {url[:60]}")
            continue

        # Build search query
        query = f"{brand} {model} stroller baby product site official"
        print(f"[{i+1:3}] SEARCH {brand} {model} ...")
        results = ddg_search(query)

        if results:
            best = pick_best_url(results, brand, model)
            row["url"] = best
            print(f"       → {best}")
            changed += 1
        else:
            print(f"       → No results found, keeping empty")

        time.sleep(0.8)  # be polite to DDG

    # Write output file
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Updated {changed} URLs.")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
