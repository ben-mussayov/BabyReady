// Test script: Fetches raw HTML from product pages and extracts JSON-LD + OG meta
// Run: node test_scraper.js

const TEST_URLS = [
  'https://www.bugaboo-distributor.co.il/product/fox5/',
  'https://www.moradbaby.co.il/items/8346445',
  'https://www.babylino.co.il/items/7857989',
  'https://www.kochavnolad.co.il/items/4414136',
];

async function fetchAndAnalyze(url) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`URL: ${url}`);
  console.log('='.repeat(80));

  try {
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'he-IL,he;q=0.9,en;q=0.8',
      },
      redirect: 'follow',
    });
    const html = await res.text();
    console.log(`  HTML size: ${html.length} bytes`);

    // 1. Extract ALL JSON-LD blocks
    const jsonLdRegex = /<script[^>]+type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
    let match;
    let jsonLdBlocks = [];
    while ((match = jsonLdRegex.exec(html)) !== null) {
      try {
        const parsed = JSON.parse(match[1].trim());
        jsonLdBlocks.push(parsed);
      } catch (e) {
        console.log(`  [JSON-LD parse error]: ${e.message}`);
      }
    }
    console.log(`  JSON-LD blocks found: ${jsonLdBlocks.length}`);

    // Find Product type
    let product = null;
    for (const block of jsonLdBlocks) {
      if (block['@type'] === 'Product') {
        product = block;
        break;
      }
      // Check for @graph
      if (block['@graph']) {
        const p = block['@graph'].find(item => item['@type'] === 'Product');
        if (p) { product = p; break; }
      }
      // Check arrays
      if (Array.isArray(block)) {
        const p = block.find(item => item['@type'] === 'Product');
        if (p) { product = p; break; }
      }
    }

    if (product) {
      console.log(`\n  === JSON-LD Product Data ===`);
      console.log(`  Name:        ${product.name || '❌ MISSING'}`);
      console.log(`  Brand:       ${product.brand?.name || product.brand || '❌ MISSING'}`);
      console.log(`  Description: ${(product.description || '❌ MISSING').substring(0, 120)}...`);
      
      // Handle image (can be string or array)
      const img = Array.isArray(product.image) ? product.image[0] : product.image;
      console.log(`  Image:       ${img || '❌ MISSING'}`);
      
      // Handle offers
      const offers = product.offers;
      if (offers) {
        const offer = Array.isArray(offers) ? offers[0] : offers;
        console.log(`  Price:       ${offer.price || offer.lowPrice || '❌ MISSING'}`);
        console.log(`  Currency:    ${offer.priceCurrency || '❌ MISSING'}`);
        console.log(`  Available:   ${offer.availability || '❌ MISSING'}`);
      } else {
        console.log(`  Offers:      ❌ MISSING`);
      }
    } else {
      console.log(`  ❌ NO JSON-LD Product found`);
      // Print all types found
      for (const block of jsonLdBlocks) {
        console.log(`  JSON-LD types: ${block['@type'] || (block['@graph'] ? '@graph' : 'unknown')}`);
      }
    }

    // 2. Extract OG meta tags
    console.log(`\n  === OpenGraph Meta Tags ===`);
    const ogTags = ['og:title', 'og:description', 'og:image', 'og:url', 'product:price:amount', 'product:price:currency'];
    for (const tag of ogTags) {
      const m = html.match(new RegExp(`<meta[^>]+(?:property|name)="${tag}"[^>]+content="([^"]+)"`, 'i'))
             || html.match(new RegExp(`<meta[^>]+content="([^"]+)"[^>]+(?:property|name)="${tag}"`, 'i'));
      console.log(`  ${tag.padEnd(30)} ${m ? m[1].substring(0, 100) : '❌ MISSING'}`);
    }

    // 3. Extract price patterns from HTML
    console.log(`\n  === HTML Price Patterns ===`);
    const pricePatterns = [
      { name: 'JSON "price"', regex: /"price"\s*:\s*"?(\d[\d,.]*)"?/i },
      { name: '₪ pattern',     regex: /₪\s*([\d,]+)/i },
      { name: 'ILS pattern',   regex: /(\d[\d,]*)\s*₪/i },
      { name: 'price class',   regex: /class="[^"]*price[^"]*"[^>]*>[\s\S]*?₪?\s*([\d,]+)/i },
    ];
    for (const p of pricePatterns) {
      const m = html.match(p.regex);
      console.log(`  ${p.name.padEnd(20)} ${m ? m[1] : '❌ not found'}`);
    }

    // 4. Check store name detection
    const hostname = new URL(url).hostname.replace('www.', '');
    console.log(`\n  Store hostname: ${hostname}`);

  } catch (e) {
    console.log(`  ERROR: ${e.message}`);
  }
}

(async () => {
  for (const url of TEST_URLS) {
    await fetchAndAnalyze(url);
  }
  console.log('\n\nDone!');
})();
