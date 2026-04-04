const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = 'https://mbyrgbtdpefncusxqzoc.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc';

const sb = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

const STORES_DATA = {
  shilav: { name_he: 'שילב', name_en: 'Shilav', logo: 'https://www.shilav.co.il/cdn/shop/files/SHILAV-1.png?v=1724591056', url: 'https://www.shilav.co.il' },
  motzetzim: { name_he: 'מוצצים', name_en: 'Motzetzim', logo: 'https://motsesim.co.il/cdn/shop/files/3265138a040434fd4d2866b4acacf4e0.webp?v=1768919819&width=400', url: 'https://motsesim.co.il' },
  babystar: { name_he: 'בייבי סטאר', name_en: 'Baby Star', logo: 'https://www.baby-star.co.il/cdn/shop/files/site-logo-01.png?v=1728044100', url: 'https://www.baby-star.co.il' },
  aglis: { name_he: 'עגליס', name_en: 'Aglis', logo: 'https://agalease-baby.co.il/wp-content/uploads/2020/09/Agalease-Logo-Outline-Horizontal-e1600329730819.png', url: 'https://agalease-baby.co.il' },
  moradbaby: { name_he: 'מוראד בייבי', name_en: 'Morad Baby', logo: 'https://d3m9l0v76dty0.cloudfront.net/system/logos/5404/original/09383995f81fd38cb98536172f5225df.png', url: 'https://www.moradbaby.co.il' },
  babylino: { name_he: 'בייבילינו', name_en: 'Babylino', logo: 'https://d3m9l0v76dty0.cloudfront.net/system/logos/5400/original/02cd7229da8a263b445fcc9b8e306bef.png', url: 'https://www.babylino.co.il' },
  kochavnolad: { name_he: 'כוכב נולד', name_en: 'Kochav Nolad', logo: 'https://d3m9l0v76dty0.cloudfront.net/system/logos/4413/original/dae5a1b42056b254ffe6b06861c6ceb8.png', url: 'https://www.kochavnolad.co.il' },
  'bugaboo-distributor': { name_he: 'בוגבו ישראל', name_en: 'Bugaboo Israel', logo: 'https://www.bugaboo-distributor.co.il/wp-content/uploads/2019/10/logo.svg', url: 'https://www.bugaboo-distributor.co.il' },
  amazon: { name_he: 'Amazon', name_en: 'Amazon', logo: 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg', url: 'https://www.amazon.com' },
  aliexpress: { name_he: 'AliExpress', name_en: 'AliExpress', logo: 'https://upload.wikimedia.org/wikipedia/commons/3/3b/Aliexpress_logo.svg', url: 'https://www.aliexpress.com' }
};

async function run() {
  console.log('Starting store logo refresh...');
  for (const [id, s] of Object.entries(STORES_DATA)) {
    console.log(`Updating ${id}...`);
    const { error } = await sb.from('stores').upsert({
      id: id,
      name_he: s.name_he,
      name_en: s.name_en,
      url: s.url,
      logo_url: s.logo,
      active: true
    }, { onConflict: 'id' });
    
    if (error) {
      console.error(`Error updating ${id}:`, error.message);
    } else {
      console.log(`Successfully updated ${id}`);
    }
  }
  console.log('Store logo refresh complete!');
}

run();
