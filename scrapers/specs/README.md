# Product spec scrapers

Daily **prices** come from the inflation study's scrapers
(`InflationResearchStudy/InflationItems/Datas`). These scrapers collect what
each product **is** (brand, colour, storage, RAM, screen size, condition, link,
image) and write it to `data/specs/<retailer>_specs.csv`.

Each price row is joined to its variant through the retailer's own product id:

| Retailer | Daily price CSV (inflation study) | Daily column | = specs column |
|---|---|---|---|
| Pozitif | `08_Communication/PozitifTeknoloji/pozitifTeknoloji_YYYY-MM-DD.csv` | `product_id` | `retailer_product_id` |
| Samsung | `08_Communication/Samsung/samsung_YYYY-MM-DD.csv` | `id` | `retailer_product_id` |

On 2026-10-28, 99% of the rows in each daily file joined (Pozitif 1333/1347, Samsung 343/348).

## Run

```bash
pip install -r scrapers/requirements.txt
python scrapers/specs/pozitif_specs.py   # ~15 requests, ~20 s
python scrapers/specs/samsung_specs.py   # 21 requests, ~35 s
```

A run **merges** into the existing CSV. New products are added, and known
products are updated with `first_seen` kept. Products that are no longer listed
are kept, so older price rows still join. That means it can run once or on a
schedule to pick up new products.

## Columns

| Column | Meaning |
|---|---|
| `retailer_product_id` | Join key to the daily price CSV |
| `model_code` | Manufacturer part number (Apple `MTP03TU/A`, Samsung `SM-A185FLBDTUR`). The key for matching the same product across stores |
| `name`, `brand`, `category`, `family` | `category` is the store's path, e.g. `Outlet > iPhone Outlet > iPhone 15 Outlet` |
| `color` | As the store writes it, in Turkish |
| `storage_gb`, `ram_gb` | Numbers; 1 TB = 1024 |
| `screen_size_in` | Inches |
| `capacity` | Non-storage capacity as written: `9 kg`, `508 L`, `12000 BTU/h` |
| `processor`, `connectivity` | e.g. `M5`, `Wi-Fi + Cell` |
| `condition` | `new`, `display` (teşhir), `used` (ikinci el). Don't compare a display unit's price with a new one |
| `is_bundle` | Product sets (Pozitif "Avantajlı ... Setleri") |
| `url`, `image_url` | Product page and main image |
| `attributes` | Every raw attribute the site gave, as JSON |
| `first_seen`, `last_seen` | Dates in Istanbul time |

## Gaps

- **Samsung:** the API has no RAM or processor. A few products that the inflation
  scraper finds through Samsung's sitemap (Movingstyle screen, some accessories)
  are not in any category and are missing.
- **Pozitif:** `Bellek` (RAM) is only set on Macs/iPads that offer a RAM choice. iMac
  and MacBook names also carry it ("16GB 256GB"), which name cleaning can extract.
