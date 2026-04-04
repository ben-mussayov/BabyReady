import csv
import os

try:
    print(f"Reading from {os.path.abspath('../baby_products_catalog_with_urls.csv')}")
    with open('../baby_products_catalog_with_urls.csv', 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    filtered = [r for r in rows if r['category'] in ['עגלות', 'כיסאות בטיחות', 'לולים ועריסות']]
    updates = {
        'Bugaboo Fox 5 Renew': 'https://www.bugaboo-distributor.co.il/product/fox5/',
        'Bugaboo Dragonfly': 'https://www.bugaboo-distributor.co.il/product/bugaboo-dragonfly/',
        'Bugaboo Donkey 6': 'https://www.bugaboo-distributor.co.il/product/donkey-5/', 
        'UPPAbaby Vista V3': 'https://www.shilav.co.il/baby-gear/strollers/uppababy?type=14545',
        'UPPAbaby Cruz V3': 'https://www.shilav.co.il/1454656',
        'Cybex Priam 4': 'https://cybexonline.co.il/collections/%D7%A4%D7%A8%D7%99%D7%90%D7%9D-priam',
        'Cybex e-Priam': 'https://cybexonline.co.il/collections/e-priam-%D7%A2%D7%92%D7%9C%D7%94-%D7%97%D7%A9%D7%9E%D7%9C%D7%99%D7%AA',
        'Bugaboo Stardust Playard': 'https://www.bugaboo-distributor.co.il/product/stardust/'
    }
    
    for r in filtered:
        name = f"{r['brand']} {r['model']}"
        if name in updates:
            r['url'] = updates[name]
            
    with open('../baby_products_catalog_filtered.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(filtered)
        
    print('✅ Filtered CSV written successfully.')
except Exception as e:
    print(f"Error: {e}")
