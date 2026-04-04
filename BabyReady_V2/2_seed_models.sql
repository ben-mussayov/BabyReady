-- ═══════════════════════════════════════════════
-- SEED: Product Models from Research
-- Run AFTER schema.sql
-- ═══════════════════════════════════════════════

-- Helper: insert models using brand name lookup
-- STROLLERS
with b as (select id from brands where name='Bugaboo')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'stroller', b.id, model_name, description, low, high from b,
  (values
    ('Fox 5 Renew',  'All-terrain iconic, sustainable materials', 4500, 6000),
    ('Dragonfly',    'Compact city, one-hand fold',               3800, 5000),
    ('Kangaroo',     'Converts single to double',                 5000, 6500),
    ('Donkey 6',     'Wide, extends to two children',             5500, 7000),
    ('Butterfly 2',  'Ultra-compact, cabin approved',             2800, 3500)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Anex')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'stroller', b.id, model_name, description, low, high from b,
  (values
    ('IQ',      'Transformer: pram → stroller → buggy',   3000, 4500),
    ('Eli',     'Lightweight EPP frame',                   2500, 3500),
    ('Mev',     'Ergonomic with height adapters',          2500, 3500),
    ('Flo',     '4-season, triple suspension',             2800, 4000),
    ('Air-X2',  'Travel buggy, 3-second fold',             1800, 2500)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Cybex')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'stroller', b.id, model_name, description, low, high from b,
  (values
    ('Priam 4',   'Premium flagship, all-wheel suspension',      4500, 6000),
    ('e-Priam',   'Smart, electric assist on hills',             6000, 8000),
    ('Gazelle S', 'Modular, 20+ configs, single or twin',        3800, 5500),
    ('Mios 3',    'Slim city, lightweight',                      2800, 3800),
    ('Libelle 2', 'Smallest lightest Cybex buggy',               1500, 2200)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='UPPAbaby')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'stroller', b.id, model_name, description, low, high from b,
  (values
    ('Vista V3',  'Up to 3 children, flagship',             4500, 6000),
    ('Cruz V3',   'Full-size, narrow frame, agile',         3500, 4800),
    ('Minu V3',   'Compact with full-size performance',     2800, 3800),
    ('Ridge V2',  'All-terrain running stroller',           2500, 3500),
    ('G-Luxe',    'Lightweight umbrella stroller',          1200, 1800)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Nuna')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'stroller', b.id, model_name, description, low, high from b,
  (values
    ('Mixx Next',   'All-terrain, compact fold',             3500, 5000),
    ('Demi Icon',   'Modular, adjustable suspension',        4000, 5500),
    ('Triv Next',   'Lightweight city, compact fold',        2800, 3800),
    ('TRVL lx',     'Auto self-fold',                        2200, 3000),
    ('Swiv',        '360° swivel wheels for max maneuver',   2000, 2800)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

-- Karin pick for stroller
with b as (select id from brands where name='Baby Star'),
     m as (insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high, is_karin_pick, karin_note)
            select 'stroller', b.id, '65279', 'Great value, functional, highly recommended', 800, 1200, true, 'מחיר-ביצועים מעולה — ממוצר עגליס'
            from b on conflict (category_id, brand_id, model_name) do nothing returning id)
select 1;

-- CAR SEATS
with b as (select id from brands where name='Cybex')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'car-seat', b.id, model_name, description, low, high from b,
  (values
    ('Cloud T',     'Rotating infant carrier, i-Size',      1800, 2500),
    ('Sirona S2',   '360° rotating, i-Size, up to 4yr',    1600, 2200),
    ('Aton G',      'Infant carrier, lightweight',           1200, 1700),
    ('Anoris T2',   'Built-in airbag technology',            2500, 3200)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Nuna')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'car-seat', b.id, model_name, description, low, high from b,
  (values
    ('Pipa Urbn',   'Infant carrier, no base required',     1400, 1900),
    ('Pipa Aire RX','Ultra-lightweight infant carrier',      1600, 2100),
    ('Rava Next',   'Advanced convertible seat',             1800, 2400),
    ('Revv Maxx',   'Rotating convertible seat',             2000, 2600),
    ('Exec Next',   'All-in-One for all ages',               2200, 3000)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='UPPAbaby')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'car-seat', b.id, model_name, description, low, high from b,
  (values
    ('Aria V2',  'Lightest infant carrier ~2.7kg',    1500, 2000),
    ('Mesa V3',  'NHTSA top rated infant carrier',    1800, 2400),
    ('Rove',     'Multi-stage convertible seat',      2000, 2600)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Chicco')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high, is_karin_pick, karin_note) select
  'car-seat', b.id, model_name, description, low, high, karin, knote from b,
  (values
    ('Fit 360',     '360° rotating — safest & easiest',  1500, 2000, true,  'הכי בטוח וקל לשימוש — ממוצר קרין'),
    ('NextFit Zip', 'Zip-off cover, convertible',         1200, 1600, false, null),
    ('KeyFit 35',   'Easy install infant carrier',         900,  1300, false, null),
    ('MyFit',       'Harness-to-booster seat',             800,  1200, false, null)
  ) as t(model_name, description, low, high, karin, knote)
on conflict (category_id, brand_id, model_name) do nothing;

-- CRIBS / PLAYARDS
with b as (select id from brands where name='Segal')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high, is_karin_pick, karin_note) select
  'crib', b.id, model_name, description, low, high, karin, knote from b,
  (values
    ('Liz Natural', 'Solid natural wood, great warranty',  700, 1000, true,  'עץ טבעי, עיצוב נקי — ממוצר קרין'),
    ('Maya',        'Adjustable height, converts to toddler', 600, 900, false, null)
  ) as t(model_name, description, low, high, karin, knote)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Sport Line')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'crib', b.id, model_name, description, low, high from b,
  (values
    ('Noah',  'Convertible with storage drawer',  800,  1200),
    ('Alma',  'Minimalist solid wood',            700,  1000),
    ('Noaa',  'With wheels, easy to move',        900,  1300)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Nuna')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'crib', b.id, model_name, description, low, high from b,
  (values
    ('Sena Aire', '360° ventilation travel playard',  900, 1300),
    ('Cove Aire', 'Compact travel crib',              800, 1100)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='UPPAbaby')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'crib', b.id, model_name, description, low, high from b,
  (values
    ('Remi Playard', 'Lightweight foldable playard',        1200, 1800),
    ('Soma',         'Smart bassinet with auto-soothe',     2200, 3000)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='Bugaboo')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'crib', b.id, model_name, description, low, high from b,
  (values
    ('Stardust Playard', 'Folds in seconds, ultra-compact', 800, 1100)
  ) as t(model_name, description, low, high)
on conflict (category_id, brand_id, model_name) do nothing;

-- CHANGING TABLE
with b as (select id from brands where name='Panda')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high, is_karin_pick, karin_note) select
  'changing', b.id, model_name, description, low, high, karin, knote from b,
  (values
    ('Trica Silent', 'Silent drawers, excellent quality',  600, 800, true,  'מגירות שקטות — ממוצר קרין, נמכר בשילב'),
    ('Oslo',         'Wide surface, deep storage',         650, 900, false, null)
  ) as t(model_name, description, low, high, karin, knote)
on conflict (category_id, brand_id, model_name) do nothing;

with b as (select id from brands where name='IKEA')
insert into product_models (category_id, brand_id, model_name, description, price_range_low, price_range_high) select
  'changing', b.id, 'Hemnes', 'Budget-friendly, sturdy, white', 350, 500 from b
on conflict (category_id, brand_id, model_name) do nothing;

