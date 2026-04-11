-- ═══════════════════════════════════════════════
-- BabyReady - Price Evaluation & Buying Clubs
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════

-- ─── BUYING CLUBS ───────────────────────────────
create table if not exists buying_clubs (
  id          text primary key,  -- 'hever', 'police', 'histadrut', etc.
  name_he     text not null,
  name_en     text,
  logo_url    text,
  active      boolean default true,
  created_at  timestamptz default now()
);

-- ─── CLUB DISCOUNTS ─────────────────────────────
create table if not exists club_discounts (
  id                uuid primary key default uuid_generate_v4(),
  club_id           text references buying_clubs(id) on delete cascade,
  store_id          text references stores(id) on delete cascade,
  discount_percent  float default 0,
  unique(club_id, store_id)
);

-- ─── USER EVALUATION CART ───────────────────────
-- Stores which store and which club the user selected for an item.
create table if not exists user_eval_cart (
  id                uuid primary key default uuid_generate_v4(),
  user_id           uuid references profiles(id) on delete cascade,
  user_item_id      uuid references user_items(id) on delete cascade,
  selected_store_id text references stores(id) on delete cascade,
  is_eilat          boolean default false,
  applied_club_id   text references buying_clubs(id),
  created_at        timestamptz default now(),
  unique(user_id, user_item_id)
);

-- ─── RLS POLICIES ──────────────────────────────
alter table buying_clubs    enable row level security;
alter table club_discounts  enable row level security;
alter table user_eval_cart  enable row level security;

-- Public read for catalog data
create policy "Public read clubs" on buying_clubs for select using (true);
create policy "Public read club discounts" on club_discounts for select using (true);

-- User manage own eval cart
create policy "Users manage own eval cart" on user_eval_cart
  for all using (auth.uid() = user_id);

-- Admin manage clubs and discounts
create policy "Admins manage clubs" on buying_clubs
  for all using ((select is_admin from profiles where id = auth.uid()));
create policy "Admins manage discounts" on club_discounts
  for all using ((select is_admin from profiles where id = auth.uid()));

-- ─── SEED DATA ─────────────────────────────────
insert into buying_clubs (id, name_he, name_en) values
  ('hever', 'חבר', 'Hever'),
  ('police', 'קרנות השוטרים', 'Police Funds'),
  ('histadrut', 'ביחד בשבילך (ההסתדרות)', 'Histadrut')
on conflict (id) do nothing;
