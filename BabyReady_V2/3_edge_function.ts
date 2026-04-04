// Supabase Edge Function: scrape-product
// Deploy: supabase functions deploy scrape-product
// Called when user pastes a product URL
//
// Strategy: JSON-LD first → OpenGraph meta → HTML regex fallback
// This ensures consistent extraction across WooCommerce, Konimbo, and other platforms.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface ProductData {
  name: string;
  brand: string;
  description: string;
  price: number;
  currency: string;
  image_url: string;
  store_name: string;
  store_id: string;
  product_url: string;
  in_stock: boolean;
}

// ─── Known store ID mapping (for labeling) ───
const STORE_ID_MAP: Record<string, string> = {
  "shilav.co.il": "shilav",
  "aglis.co.il": "aglis",
  "babystar.co.il": "babystar",
  "motzetzim.co.il": "motzetzim",
  "motsesim.co.il": "motzetzim",
  "amazon.com": "amazon",
  "amazon.co.il": "amazon",
  "aliexpress.com": "aliexpress",
  "bugaboo-distributor.co.il": "bugaboo-distributor",
  "moradbaby.co.il": "moradbaby",
  "babylino.co.il": "babylino",
  "kochavnolad.co.il": "kochavnolad",
};

// ─── Known brand names for fallback extraction ───
const KNOWN_BRANDS = [
  "Bugaboo","Cybex","Nuna","Doona","Joie","BabyZen","Stokke","Maxi Cosi","Chicco",
  "UPPAbaby","Anex","Peg Perego","BabyBjorn","Graco","Britax","Inglesina","iCandy","Joolz",
  "בוגבו","סייבקס","נונה","דונה","ג'ואי","בייביזן","סטוקה","מקסי קוזי","צ'יקו",
];

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  try {
    const { url } = await req.json();
    if (!url || !url.startsWith("http")) {
      return new Response(JSON.stringify({ error: "Invalid URL" }), { 
        status: 400, headers: { ...CORS, "Content-Type": "application/json" } 
      });
    }

    // Detect store from hostname
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.replace("www.", "");
    const storeKey = Object.keys(STORE_ID_MAP).find(k => hostname.includes(k));
    const store_id = storeKey ? STORE_ID_MAP[storeKey] : "other";
    
    // Derive a human-readable store name from hostname
    const storeName = deriveStoreName(hostname);

    // Fetch the page
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
      },
      redirect: "follow",
    });

    if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
    const html = await response.text();

    // ═══════════════════════════════════════════════
    //  LAYER 1: JSON-LD structured data (most reliable)
    // ═══════════════════════════════════════════════
    const jsonLd = extractJsonLdProduct(html);

    // ═══════════════════════════════════════════════
    //  LAYER 2: OpenGraph meta tags (good fallback)
    // ═══════════════════════════════════════════════
    const og = extractOpenGraph(html);

    // ═══════════════════════════════════════════════
    //  LAYER 3: HTML regex (last resort)
    // ═══════════════════════════════════════════════
    const htmlFallback = extractFromHtml(html, url);

    // ═══════════════════════════════════════════════
    //  MERGE: Each field resolved independently
    // ═══════════════════════════════════════════════
    const rawName = jsonLd.name || og.title || htmlFallback.title || "Unknown Product";
    const rawBrand = jsonLd.brand || extractBrandFromText(rawName) || "";
    const rawDescription = cleanDescription(jsonLd.description || og.description || "");
    
    const result: ProductData = {
      name: rawName,
      brand: rawBrand,
      description: rawDescription,
      price: jsonLd.price || og.price || htmlFallback.price || 0,
      currency: jsonLd.currency || og.currency || (hostname.includes(".co.il") ? "ILS" : "USD"),
      image_url: resolveUrl(jsonLd.image || og.image || htmlFallback.image || "", url),
      store_name: storeName,
      store_id,
      product_url: url,
      in_stock: jsonLd.inStock !== false,
    };

    return new Response(JSON.stringify({ data: result }), {
      headers: { ...CORS, "Content-Type": "application/json" },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...CORS, "Content-Type": "application/json" },
    });
  }
});

// ═══════════════════════════════════════════════
//  EXTRACTION: JSON-LD
// ═══════════════════════════════════════════════

interface JsonLdResult {
  name: string;
  brand: string;
  description: string;
  price: number;
  currency: string;
  image: string;
  inStock: boolean;
}

function extractJsonLdProduct(html: string): JsonLdResult {
  const empty: JsonLdResult = { name: "", brand: "", description: "", price: 0, currency: "", image: "", inStock: true };
  
  const regex = /<script[^>]+type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  
  while ((match = regex.exec(html)) !== null) {
    try {
      const parsed = JSON.parse(match[1].trim());
      const product = findProductInJsonLd(parsed);
      if (product) {
        // Extract offers
        let price = 0, currency = "", inStock = true;
        const offers = product.offers;
        if (offers) {
          const offer = Array.isArray(offers) ? offers[0] : offers;
          price = parseFloat(String(offer.price || offer.lowPrice || "0").replace(/,/g, "")) || 0;
          currency = offer.priceCurrency || "";
          if (offer.availability) {
            inStock = offer.availability.toLowerCase().includes("instock");
          }
        }

        // Extract image (can be string, array, or object)
        let image = "";
        if (typeof product.image === "string") {
          image = product.image;
        } else if (Array.isArray(product.image)) {
          image = product.image[0] || "";
        } else if (product.image?.url) {
          image = product.image.url;
        }

        // Extract brand
        let brand = "";
        if (typeof product.brand === "string") {
          brand = product.brand;
        } else if (product.brand?.name) {
          brand = product.brand.name;
        }

        return {
          name: product.name || "",
          brand,
          description: product.description || "",
          price,
          currency,
          image,
          inStock,
        };
      }
    } catch (e) {
      // Invalid JSON, skip this block
    }
  }
  
  return empty;
}

function findProductInJsonLd(data: any): any {
  if (!data) return null;
  
  // Direct Product type
  if (data["@type"] === "Product") return data;
  
  // Inside @graph array
  if (data["@graph"] && Array.isArray(data["@graph"])) {
    const p = data["@graph"].find((item: any) => item["@type"] === "Product");
    if (p) return p;
  }
  
  // Array of items
  if (Array.isArray(data)) {
    const p = data.find((item: any) => item["@type"] === "Product");
    if (p) return p;
  }
  
  return null;
}

// ═══════════════════════════════════════════════
//  EXTRACTION: OpenGraph meta
// ═══════════════════════════════════════════════

interface OgResult {
  title: string;
  description: string;
  image: string;
  price: number;
  currency: string;
}

function extractOpenGraph(html: string): OgResult {
  return {
    title: extractMeta(html, "og:title"),
    description: extractMeta(html, "og:description"),
    image: extractMeta(html, "og:image"),
    price: parseFloat(extractMeta(html, "product:price:amount") || "0") || 0,
    currency: extractMeta(html, "product:price:currency") || "",
  };
}

function extractMeta(html: string, property: string): string {
  const m = html.match(new RegExp(`<meta[^>]+(?:property|name)="${property}"[^>]+content="([^"]+)"`, "i"))
           || html.match(new RegExp(`<meta[^>]+content="([^"]+)"[^>]+(?:property|name)="${property}"`, "i"));
  return m ? decodeHTMLEntities(m[1]) : "";
}

// ═══════════════════════════════════════════════
//  EXTRACTION: HTML regex (last resort)
// ═══════════════════════════════════════════════

interface HtmlResult {
  title: string;
  price: number;
  image: string;
}

function extractFromHtml(html: string, url: string): HtmlResult {
  // Title from <title> tag
  const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
  const title = titleMatch ? decodeHTMLEntities(titleMatch[1].trim()) : "";

  // Price: try JSON "price" first, then ₪ symbol patterns
  let price = 0;
  const jsonPriceMatch = html.match(/"price"\s*:\s*"?(\d[\d.]*)"?/i);
  if (jsonPriceMatch) {
    price = parseFloat(jsonPriceMatch[1]) || 0;
  }
  if (!price) {
    const shekelMatch = html.match(/₪\s*([\d,]+(?:\.\d+)?)/);
    if (shekelMatch) {
      price = parseFloat(shekelMatch[1].replace(/,/g, "")) || 0;
    }
  }

  // Image: find first product-looking image
  let image = "";
  let idx = 0;
  while ((idx = html.indexOf("<img", idx)) !== -1) {
    const end = html.indexOf(">", idx);
    if (end === -1) break;
    const imgTag = html.substring(idx, end + 1);
    const srcMatch = imgTag.match(/(?:src|data-src)=["']([^"']+)["']/i);
    if (srcMatch && srcMatch[1]) {
      const src = srcMatch[1];
      if (!src.toLowerCase().includes("logo") && !src.toLowerCase().includes("icon") && !src.toLowerCase().includes("spinner")) {
        if (src.match(/\.(jpg|jpeg|png|webp)/i) || src.length > 20) {
          image = src;
          if (imgTag.includes("product") || imgTag.includes("main")) break;
        }
      }
    }
    idx = end;
  }

  return { title, price, image };
}

// ═══════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════

function decodeHTMLEntities(str: string): string {
  return str
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#x2F;/g, "/");
}

function extractBrandFromText(text: string): string {
  for (const brand of KNOWN_BRANDS) {
    if (text.toLowerCase().includes(brand.toLowerCase())) {
      return brand;
    }
  }
  return "";
}

function cleanDescription(desc: string): string {
  if (!desc) return "";
  // Remove HTML tags that might have leaked into JSON-LD description
  let cleaned = desc
    .replace(/<[^>]+>/g, " ")           // Strip HTML tags
    .replace(/&nbsp;/g, " ")           // Replace &nbsp;
    .replace(/\s+/g, " ")             // Collapse whitespace
    .trim();
  // Truncate to reasonable length
  if (cleaned.length > 300) {
    cleaned = cleaned.substring(0, 300).replace(/\s+\S*$/, "") + "...";
  }
  return cleaned;
}

function resolveUrl(imgUrl: string, baseUrl: string): string {
  if (!imgUrl) return "";
  if (imgUrl.startsWith("//")) return "https:" + imgUrl;
  if (imgUrl.startsWith("/")) {
    try { return new URL(imgUrl, baseUrl).href; } catch (e) { return imgUrl; }
  }
  if (!imgUrl.startsWith("http")) {
    try { return new URL(imgUrl, baseUrl).href; } catch (e) { return imgUrl; }
  }
  return imgUrl;
}

function deriveStoreName(hostname: string): string {
  // Map known hostnames to friendly Hebrew/English store names
  const nameMap: Record<string, string> = {
    "shilav.co.il": "שילב",
    "aglis.co.il": "עגליס",
    "babystar.co.il": "בייבי סטאר",
    "motzetzim.co.il": "מוצצים",
    "motsesim.co.il": "מוצצים",
    "amazon.com": "Amazon",
    "amazon.co.il": "Amazon Israel",
    "aliexpress.com": "AliExpress",
    "bugaboo-distributor.co.il": "בוגבו ישראל",
    "moradbaby.co.il": "מוראד בייבי",
    "babylino.co.il": "בייבילינו",
    "kochavnolad.co.il": "כוכב נולד",
  };
  
  const key = Object.keys(nameMap).find(k => hostname.includes(k));
  if (key) return nameMap[key];
  
  // Fallback: prettify hostname
  return hostname
    .replace(/\.co\.il$/, "")
    .replace(/\.com$/, "")
    .replace(/[._-]/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}
