import json
import time
import urllib.request
from urllib.error import URLError, HTTPError
import csv

URL = 'https://mbyrgbtdpefncusxqzoc.supabase.co'
KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MDMyOTIsImV4cCI6MjA5MDM3OTI5Mn0.CKyhfWlCMaNycwqYDM8XYv_4u2pQSUr3ez4hOIc84Xg'

HEADERS = {
    'apikey': KEY,
    'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json',
}

def test_scrape(url):
    retries = 2
    for _ in range(retries):
        try:
            req = urllib.request.Request(f"{URL}/functions/v1/scrape-product", 
                                         data=json.dumps({"url": url}).encode('utf-8'), 
                                         headers=HEADERS, method='POST')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode()).get('data', {})
                    return data.get('image_url') or data.get('image')
        except Exception as e:
            pass
        time.sleep(0.5)
    return None

def main():
    with open('../baby_products_catalog_filtered.csv', 'r', encoding='utf-8') as f:
        items = list(csv.DictReader(f))

    print(f"Testing local CSV: {len(items)} items")
    found = 0
    for i in items:
        img = test_scrape(i['url'])
        if img:
            print(f"✅ [{i['brand']} {i['model']}] {img}")
            found += 1
        else:
            print(f"❌ [{i['brand']} {i['model']}] Failed for {i['url']}")
    print(f"Done! Evaluated {found}/{len(items)} correctly with images.")

if __name__ == '__main__':
    main()
