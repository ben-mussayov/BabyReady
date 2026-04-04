import json
import time
import urllib.request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

URL = 'https://mbyrgbtdpefncusxqzoc.supabase.co'
KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MDMyOTIsImV4cCI6MjA5MDM3OTI5Mn0.CKyhfWlCMaNycwqYDM8XYv_4u2pQSUr3ez4hOIc84Xg'

HEADERS = {
    'apikey': KEY,
    'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}

def get_missing_images():
    req = urllib.request.Request(f"{URL}/rest/v1/product_models?select=id,product_url,image_url", headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        models = json.loads(response.read().decode())
        missing = [m for m in models if m.get('product_url') and not m.get('image_url')]
        return missing

def scrape_url(url):
    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(f"{URL}/functions/v1/scrape-product", 
                                         data=json.dumps({"url": url}).encode('utf-8'), 
                                         headers=HEADERS, method='POST')
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode()).get('data', {})
                    return data.get('image_url') or data.get('image')
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        time.sleep(1)
    return None

def update_image(model_id, image_url):
    req = urllib.request.Request(f"{URL}/rest/v1/product_models?id=eq.{model_id}", 
                                 data=json.dumps({"image_url": image_url}).encode('utf-8'), 
                                 headers=HEADERS, method='PATCH')
    try:
        with urllib.request.urlopen(req) as response:
            return response.status
    except HTTPError as e:
        return e.code
    except URLError:
        return 0

def main():
    try:
        missing = get_missing_images()
    except Exception as e:
        print(f"Failed to fetch models: {e}")
        return

    print(f"Found {len(missing)} models missing images but having a URL")
    
    updated = 0
    for m in missing:
        print(f"Scraping {m['product_url']} ...")
        image_url = scrape_url(m['product_url'])
        
        if image_url:
            if image_url.startswith('/'):
                try:
                    domain = f"https://{urlparse(m['product_url']).netloc}"
                    image_url = domain + image_url
                except:
                    pass
            print(f"[{m['id']}] Found image: {image_url}")
            status = update_image(m['id'], image_url)
            if status in [200, 204]:
                updated += 1
                print(f"Successfully updated {m['id']}")
            else:
                print(f"Failed to update {m['id']} with status {status}")
        else:
            print(f"[{m['id']}] No image found")
    print(f"Finished updating {updated} out of {len(missing)} models.")

if __name__ == '__main__':
    main()
