const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = 'https://mbyrgbtdpefncusxqzoc.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ieXJnYnRkcGVmbmN1c3hxem9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDgwMzI5MiwiZXhwIjoyMDkwMzc5MjkyfQ.yMUXq5ngnmMe1_VGui8HUJ_mtzG1brunnHpATdibXnc';

const sb = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function run() {
  console.log('Promoting latest users to admin...');
  const { data: profiles, error: pError } = await sb.from('profiles').select('id, username').order('created_at', { ascending: false }).limit(5);
  
  if (pError || !profiles.length) {
    console.error('No profiles found:', pError?.message);
    return;
  }

  for (const p of profiles) {
    console.log(`Promoting ${p.username} (${p.id})...`);
    const { error: uError } = await sb.from('profiles').update({ is_admin: true }).eq('id', p.id);
    if (uError) console.error('Error promoting:', uError.message);
  }
}

run();
