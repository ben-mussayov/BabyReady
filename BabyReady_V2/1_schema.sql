-- ═══════════════════════════════════════════════
-- BabyReady Database Schema
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ─── STORES ────────────────────────────────────
create table if not exists stores (
  id          text primary key,  -- 'shilav', 'aglis', etc.
  name_en     text not null,
  name_he     text not null,
  url         text not null,
  logo_url    text,
  country     text default 'IL',
  type        text default 'local', -- 'local' | 'amazon' | 'aliexpress'
  active      boolean default true
);

-- ─── PRODUCT CATEGORIES ────────────────────────
create table if not exists categories (
  id          text primary key,  -- 'stroller', 'car-seat', 'crib', etc.
  name_en     text not null,
  name_he     text not null,
  icon        text not null,
  urgency     text not null default 'medium',  -- critical/high/medium/low
  priority    int  default 10,   -- lower = shown first
  is_essential boolean default false  -- the 3 core ones
);

-- ─── BRANDS ────────────────────────────────────
create table if not exists brands (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null unique,
  logo_url    text,
  country     text,   -- brand origin
  tier        text default 'premium'  -- 'budget' | 'mid' | 'premium'
);

-- ─── PRODUCT MODELS (the "breathing DB") ───────
create table if not exists product_models (
  id            uuid primary key default uuid_generate_v4(),
  category_id   text references categories(id),
  brand_id      uuid references brands(id),
  model_name    text not null,
  description   text,
  image_url     text,
  price_range_low   int,   -- ILS
  price_range_high  int,   -- ILS
  features      jsonb default '[]',  -- ["360° rotation", "i-Size"]
  is_karin_pick boolean default false,
  karin_note    text,
  active        boolean default true,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now(),
  -- so we can find same model across stores
  unique(category_id, brand_id, model_name)
);

-- ─── PRODUCT PRICES (per store) ────────────────
create table if not exists product_prices (
  id              uuid primary key default uuid_generate_v4(),
  model_id        uuid references product_models(id) on delete cascade,
  store_id        text references stores(id),
  price           int not null,  -- ILS
  currency        text default 'ILS',
  product_url     text,          -- direct link to this product at this store
  image_url       text,          -- store-specific image
  in_stock        boolean default true,
  last_checked    timestamptz default now(),
  added_by        uuid,          -- user who added this price
  verified        boolean default false,  -- admin-verified
  created_at      timestamptz default now(),
  unique(model_id, store_id)
);

-- ─── USER PROFILES ─────────────────────────────
create table if not exists profiles (
  id              uuid primary key references auth.users(id),
  username        text unique not null,
  lang            text default 'en',
  country         text default 'Israel',
  due_date        date,
  preg_week       int,
  preg_days       int default 0,
  is_admin        boolean default false,
  created_at      timestamptz default now()
);

-- ─── USER ITEM SELECTIONS ──────────────────────
create table if not exists user_items (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid references profiles(id) on delete cascade,
  category_id     text references categories(id),
  model_id        uuid references product_models(id),   -- null = custom
  custom_name     text,     -- if not from model DB
  custom_url      text,     -- link user pasted
  custom_price    int,
  store_id        text references stores(id),
  notes           text,
  is_ordered      boolean default false,
  ordered_at      date,
  estimated_delivery_date date,
  purchased       boolean default false,
  actual_price    int,
  purchased_at    timestamptz,
  created_at      timestamptz default now()
);

-- ─── USER CUSTOM PRICES (links user pastes) ────
create table if not exists user_price_contributions (
  id              uuid primary key default uuid_generate_v4(),
  model_id        uuid references product_models(id),
  store_id        text references stores(id),
  price           int not null,
  product_url     text,
  scraped_data    jsonb,   -- raw data from URL scrape
  verified        boolean default false,
  contributed_by  uuid references profiles(id),
  created_at      timestamptz default now()
);

-- ═══════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════

alter table stores              enable row level security;
alter table categories          enable row level security;
alter table brands              enable row level security;
alter table product_models      enable row level security;
alter table product_prices      enable row level security;
alter table profiles            enable row level security;
alter table user_items          enable row level security;
alter table user_price_contributions enable row level security;

-- Everyone can read the catalog
create policy "Public read stores"         on stores         for select using (true);
create policy "Public read categories"     on categories     for select using (true);
create policy "Public read brands"         on brands         for select using (true);
create policy "Public read models"         on product_models for select using (true);
create policy "Public read prices"         on product_prices for select using (true);

-- Users manage own data
create policy "Users read own profile"     on profiles for select using (auth.uid() = id);
create policy "Users update own profile"   on profiles for update using (auth.uid() = id);
create policy "Users insert own profile"   on profiles for insert with check (auth.uid() = id);

create policy "Users manage own items"     on user_items
  for all using (auth.uid() = user_id);

create policy "Users add contributions"    on user_price_contributions
  for insert with check (auth.uid() = contributed_by);
create policy "Users read contributions"   on user_price_contributions
  for select using (true);

-- Admins can write to catalog tables
create policy "Admins manage stores"       on stores
  for all using ((select is_admin from profiles where id = auth.uid()));
create policy "Admins manage categories"   on categories
  for all using ((select is_admin from profiles where id = auth.uid()));
create policy "Admins manage brands"       on brands
  for all using ((select is_admin from profiles where id = auth.uid()));
create policy "Admins manage models"       on product_models
  for all using ((select is_admin from profiles where id = auth.uid()));
create policy "Admins manage prices"       on product_prices
  for all using ((select is_admin from profiles where id = auth.uid()));

-- ═══════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════

-- Stores
insert into stores (id, name_en, name_he, url, type) values
  ('shilav',      'Shilav',      'שילב',        'https://www.shilav.co.il',     'local'),
  ('aglis',       'Aglis',       'עגליס',       'https://www.aglis.co.il',      'local'),
  ('babystar',    'Baby Star',   'בייבי סטאר',  'https://www.babystar.co.il',   'local'),
  ('motzetzim',   'Motzetzim',   'מוצצים',      'https://www.motzetzim.co.il',  'local'),
  ('amazon',      'Amazon',      'Amazon',       'https://www.amazon.com',        'amazon'),
  ('aliexpress',  'AliExpress',  'AliExpress',   'https://www.aliexpress.com',   'aliexpress')
on conflict (id) do nothing;

-- Categories (is_essential = true for the 3 core ones)
insert into categories (id, name_en, name_he, icon, urgency, priority, is_essential) values
  ('stroller',    'Stroller',           'עגלת תינוק',       '👶', 'critical', 1,  true),
  ('car-seat',    'Car Seat',           'כיסא בטיחות',      '🚗', 'critical', 2,  true),
  ('crib',        'Baby Crib/Playard',  'מיטה / עריסה',     '🛏️', 'critical', 3,  true),
  ('changing',    'Changing Table',     'שידה מתחלפת',      '🧷', 'critical', 4,  false),
  ('diapers',     'Diapers & Wipes',    'חיתולים ומגבונים', '🧸', 'critical', 5,  false),
  ('clothes',     'Baby Clothes',       'בגדי תינוק',       '👕', 'critical', 6,  false),
  ('bottles',     'Baby Bottles',       'בקבוקי הזנה',      '🍼', 'critical', 7,  false),
  ('hospital',    'Hospital Bag',       'תיק חדר לידה',     '👜', 'critical', 8,  false),
  ('bathtub',     'Baby Bathtub',       'אמבטיה לתינוק',    '🛁', 'high',     9,  false),
  ('monitor',     'Baby Monitor',       'מוניטור תינוק',    '📷', 'high',     10, false),
  ('pump',        'Breast Pump',        'משאבת חלב',        '🤱', 'high',     11, false),
  ('carrier',     'Baby Carrier',       'מנשא תינוק',       '🫂', 'high',     12, false),
  ('nursing',     'Nursing Pillow',     'כרית הנקה',        '🛋️', 'high',     13, false),
  ('health',      'First Aid Kit',      'ערכת בריאות',      '🏥', 'high',     14, false),
  ('towels',      'Baby Towels',        'מגבות רחצה',       '🏊', 'high',     15, false),
  ('swaddles',    'Swaddles',           'שמיכות עטיפה',     '🌯', 'high',     16, false),
  ('bassinet',    'Bassinet',           'סל תינוק נייד',    '🌙', 'medium',   17, false),
  ('bag',         'Stroller Bag',       'תיק לעגלה',        '👝', 'medium',   18, false),
  ('pacifier',    'Pacifier',           'מוצץ',             '😶', 'medium',   19, false),
  ('nightlight',  'Night Light',        'מנורת לילה',       '🌕', 'medium',   20, false),
  ('diaperpail',  'Diaper Pail',        'שפיכולית',         '🗑️', 'medium',   21, false),
  ('playmat',     'Play Mat',           'שטיח פעילות',      '🎯', 'low',      22, false),
  ('swing',       'Swing / Bouncer',    'נדנדה / בוינסר',   '🎠', 'low',      23, false),
  ('whitenoise',  'White Noise Machine','מכונת רעש לבן',    '🔊', 'low',      24, false),
  ('highchair',   'High Chair',         'כיסא אוכל גבוה',   '🪑', 'low',      25, false)
on conflict (id) do nothing;

-- Brands
insert into brands (name, tier) values
  ('Bugaboo',   'premium'),
  ('Anex',      'premium'),
  ('Cybex',     'premium'),
  ('UPPAbaby',  'premium'),
  ('Nuna',      'premium'),
  ('Chicco',    'mid'),
  ('Segal',     'mid'),
  ('Sport Line','mid'),
  ('Panda',     'mid'),
  ('Storkcraft','mid'),
  ('Baby Star', 'budget'),
  ('IKEA',      'budget'),
  ('Haakaa',    'mid'),
  ('Boba',      'mid')
on conflict (name) do nothing;

