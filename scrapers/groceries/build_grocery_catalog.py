"""Build a cleaned grocery product catalog from the inflation study's daily CSVs.

Reads every daily CSV under InflationResearchStudy/InflationItems/Datas/01_Food
(read-only), cleans names and prices, and writes ONE ROW PER STORE PRODUCT with:
brand, size, pack count, variant (fat, lactose, organic, flavour), unit price,
latest / lowest / highest price, first and last date seen, and data-quality flags.

The daily prices themselves are not copied: they stay in the inflation study's repo
(about 8.6 million rows). This catalog is the "collect product info once" side.

Usage:
    python scrapers/groceries/build_grocery_catalog.py
    python scrapers/groceries/build_grocery_catalog.py --datas "D:/path/to/InflationItems/Datas"

Outputs:
    data/groceries/grocery_products.csv   one row per (retailer, product)
    data/groceries/grocery_summary.csv    one row per retailer: counts and coverage
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_DATAS = REPO.parent / "InflationResearchStudy" / "InflationItems" / "Datas"
OUT_DIR = REPO / "data" / "groceries"
csv.field_size_limit(10**9)

# Header spellings seen in 01_Food since March 2026 (compared lower-cased).
NAME_COLS = ("product_name", "price_name", "productname", "name", "isim", "ad", "ürün adı")
PRICE_COLS = ("price", "price (tl)", "price_tl", "product_price", "fiyat")
ID_COLS = ("product_id", "product-id", "urun_id", "sku", "product_code")
BARCODE_COLS = ("barkod", "barcode")
URL_COLS = ("product_url", "url", "link")
BRAND_COLS = ("marka", "brand")
CAT_COLS = ("category_number",)
SUB_COLS = ("sub_category_number", "subcategory_number")

PLACEHOLDER_PRICES = {999.0, 9999.0, 99999.0}
MISSING = {"", "n/a", "na", "nan", "null", "none", "-"}
DATE_PATTERNS = [
    (re.compile(r"(20\d\d-\d\d-\d\d)"), "%Y-%m-%d"),
    (re.compile(r"(20\d\d_\d\d_\d\d)"), "%Y_%m_%d"),
    (re.compile(r"(?<!\d)(20\d{6})(?!\d)"), "%Y%m%d"),
    (re.compile(r"(?<!\d)(\d\d\.\d\d\.20\d\d)(?!\d)"), "%d.%m.%Y"),
    (re.compile(r"(?<!\d)(\d\d-\d\d-20\d\d)(?!\d)"), "%d-%m-%Y"),
]
# Kim's early files carry month-day only ("products9-5.csv", "products-02-23.csv"); all data is from 2026.
MONTH_DAY = re.compile(r"products-?(\d{1,2})-(\d{1,2})\.csv$")
MONTH_DAY_YEAR = 2026

UNITS = {
    "ml": ("ml", 1), "mlt": ("ml", 1), "cc": ("ml", 1), "cl": ("ml", 10),
    "l": ("ml", 1000), "lt": ("ml", 1000), "ltr": ("ml", 1000), "litre": ("ml", 1000),
    "g": ("g", 1), "gr": ("g", 1), "grm": ("g", 1), "gram": ("g", 1),
    "kg": ("g", 1000), "kilo": ("g", 1000), "kilogram": ("g", 1000),
    "adet": ("adet", 1), "tablet": ("adet", 1), "kapsul": ("adet", 1), "yaprak": ("adet", 1),
    "rulo": ("adet", 1), "poset": ("adet", 1),
}
UNIT_ALT = "|".join(sorted(map(re.escape, UNITS), key=len, reverse=True))
NUM = r"\d+(?:[.,]\d+)?"
# A size is never glued to a model code: "GS-4CC-02" is not 4 ml.
PACK_BEFORE = re.compile(rf"(?<![\w.,-])(\d{{1,2}})\s*[x*]\s*({NUM})\s*({UNIT_ALT})\b(?!-)")
PACK_AFTER = re.compile(rf"(?<![\w.,-])({NUM})\s*({UNIT_ALT})\s*[x*]\s*(\d{{1,2}})\b")
SIZE = re.compile(rf"(?<![\w.,-])({NUM})\s*({UNIT_ALT})\b(?!-)")
# "1.480 ml", "1,850 g": a Turkish thousands separator in a small unit.
SMALL_UNITS = {"ml", "mlt", "cc", "g", "gr", "grm", "gram"}
COUNT_LI = re.compile(r"(?<![\w.,])(\d{1,3})\s*'?\s*(?:li|lu)\b")
PER_KG = re.compile(r"\b(?:kg|kilo)\b")
PER_PIECE = re.compile(r"\b(?:adet|tane)\b")

FAT = [("tam yagli", "tam yağlı"), ("yarim yagli", "yarım yağlı"), ("az yagli", "az yağlı"), ("yagsiz", "yağsız")]
FLAVOURS = ["cilekli", "cikolatali", "muzlu", "vanilyali", "kakaolu", "findikli", "bitter", "sekersiz",
            "balli", "karamelli", "limonlu", "naneli", "acili", "sade"]


def fold(text: str) -> str:
    """Turkish-aware lower case folded to ASCII: 'İthal Süt' -> 'ithal sut'."""
    text = text.replace("I", "ı").replace("İ", "i").lower()
    text = text.translate(str.maketrans("ığüşöç", "igusoc"))
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def clean_name(raw: str) -> str:
    s = html.unescape(raw or "")
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'").replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip(" ,;-\"")
    return "" if s.lower() in MISSING else s


def name_key(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.,x' ]", " ", fold(name))).strip()


def file_date(name: str) -> str:
    for pattern, fmt in DATE_PATTERNS:
        m = pattern.search(name)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt).date().isoformat()
            except ValueError:
                pass
    m = MONTH_DAY.search(name)
    if m:
        try:
            return date(MONTH_DAY_YEAR, int(m.group(1)), int(m.group(2))).isoformat()
        except ValueError:
            pass
    return ""


def parse_price(raw: str, dot_is_thousands: bool):
    s = re.sub(r"[^\d,.\-]", "", (raw or "").strip())
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif dot_is_thousands or s.count(".") > 1:
        s = s.replace(".", "")
    try:
        p = round(float(s), 2)
    except ValueError:
        return None
    return p if 0 < p < 1e7 else None


def pick(row: dict, names) -> str:
    for n in names:
        v = row.get(n)
        if v is not None and v.strip() and v.strip().lower() not in MISSING:
            return v.strip()
    return ""


def read_rows(path: Path):
    """Yield dicts with lower-cased keys; headerless 2-column files become name/price."""
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
        first = fh.readline()
        delim = ";" if first.count(";") > first.count(",") else ","
        fh.seek(0)
        reader = csv.reader(fh, delimiter=delim)
        header = next(reader, None)
        if not header:
            return
        lower = [h.strip().lower() for h in header]
        if set(lower) & set(NAME_COLS):
            for vals in reader:
                if len(vals) == len(lower):
                    yield dict(zip(lower, vals))
        elif len(header) == 2 and parse_price(header[1], False) is not None:
            yield {"product_name": header[0], "price": header[1]}
            for vals in reader:
                if len(vals) == 2:
                    yield {"product_name": vals[0], "price": vals[1]}


def load_brands():
    data = json.loads((HERE / "brands.json").read_text(encoding="utf-8"))
    over = json.loads((HERE / "brand_overrides.json").read_text(encoding="utf-8"))
    remove = {fold(x) for x in over.get("remove", [])}
    brands = {b["key"]: b["name"] for b in data["brands"] if b["key"] not in remove}
    for name in over.get("add", []):
        brands[name_key(name).replace(".", "").strip()] = name
    return brands


def find_brand(key: str, brands: dict) -> str:
    """Longest known brand at the start of the name, else a multi-word brand inside it."""
    tokens = key.replace(",", " ").split()
    for n in range(min(4, len(tokens)), 0, -1):
        cand = " ".join(tokens[:n])
        if cand in brands:
            return brands[cand]
    joined = " " + " ".join(tokens) + " "
    for b in MULTI_WORD_BRANDS:
        if f" {b} " in joined:
            return BRANDS[b]
    return ""


def num(s: str, unit: str = "") -> float:
    if unit in SMALL_UNITS and re.fullmatch(r"\d{1,2}[.,]\d{3}", s):
        return float(s[:-4] + s[-3:])
    return float(s.replace(",", "."))


def extract(key: str) -> dict:
    """Size per item, pack count, how it is sold, and variant words from a folded name."""
    out = {"size_value": "", "size_unit": "", "pack_count": "", "sold_by": "pack",
           "fat": "", "lactose_free": "", "organic": "", "flavour": ""}
    m = PACK_BEFORE.search(key)
    m2 = None if m else PACK_AFTER.search(key)
    if m or m2:
        pack, n, unit = m.groups() if m else (m2.group(3), m2.group(1), m2.group(2))
        base, factor = UNITS[unit]
        out.update(size_value=f"{num(n, unit) * factor:g}", size_unit=base, pack_count=pack)
    else:
        sizes = SIZE.findall(key)
        if sizes:
            n, unit = sizes[-1]
            base, factor = UNITS[unit]
            out.update(size_value=f"{num(n, unit) * factor:g}", size_unit=base)
            c = COUNT_LI.search(key)
            if c and int(c.group(1)) <= 48:
                out["pack_count"] = c.group(1)
        elif PER_KG.search(key):
            out.update(size_value="1000", size_unit="g", sold_by="kg")
        elif COUNT_LI.search(key):
            out.update(size_value=COUNT_LI.search(key).group(1), size_unit="adet")
        elif PER_PIECE.search(key):
            out.update(size_value="1", size_unit="adet", sold_by="piece")
    out["fat"] = next((label for word, label in FAT if word in key), "")
    out["lactose_free"] = "1" if "laktozsuz" in key else ""
    out["organic"] = "1" if "organik" in key else ""
    out["flavour"] = next((f for f in FLAVOURS if re.search(rf"\b{f}\b", key)), "")
    return out


def unit_price(price: float, attrs: dict):
    """Price per kg / L / piece, so different pack sizes can be compared."""
    if not attrs["size_value"]:
        return "", ""
    total = float(attrs["size_value"]) * (int(attrs["pack_count"]) if attrs["pack_count"] else 1)
    if total <= 0:
        return "", ""
    unit = attrs["size_unit"]
    if unit == "g":
        return f"{price / total * 1000:.2f}", "TL/kg"
    if unit == "ml":
        return f"{price / total * 1000:.2f}", "TL/L"
    return f"{price / total:.2f}", "TL/adet"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datas", type=Path, default=DEFAULT_DATAS, help="InflationItems/Datas folder")
    args = ap.parse_args()
    food = args.datas / "01_Food"
    if not food.is_dir():
        sys.exit(f"Not found: {food}. Pass --datas.")

    global BRANDS, MULTI_WORD_BRANDS
    BRANDS = load_brands()
    MULTI_WORD_BRANDS = sorted((b for b in BRANDS if " " in b), key=len, reverse=True)

    products = {}
    stats = defaultdict(Counter)
    for store_dir in sorted(p for p in food.iterdir() if p.is_dir()):
        store = store_dir.name
        for path in sorted(store_dir.rglob("*.csv")):
            day = file_date(path.name)
            if not day:
                stats[store]["files_undated"] += 1
                continue
            rows = list(read_rows(path))
            if not rows:
                stats[store]["files_unreadable"] += 1
                continue
            stats[store]["files_read"] += 1
            raw_prices = [pick(r, PRICE_COLS) for r in rows]
            three = sum(1 for p in raw_prices if re.fullmatch(r"\d{1,3}\.\d{3}", p))
            dot_thousands = three >= 0.3 * max(len(raw_prices), 1)
            if dot_thousands:
                stats[store]["files_thousands_fixed"] += 1
            for r, raw_price in zip(rows, raw_prices):
                stats[store]["rows_read"] += 1
                name = clean_name(pick(r, NAME_COLS))
                price = parse_price(raw_price, dot_thousands)
                if not name or price is None:
                    stats[store]["rows_dropped_no_name_or_price"] += 1
                    continue
                key = name_key(name)
                p = products.get((store, key))
                if p is None:
                    p = products[(store, key)] = {
                        "name": name, "first": day, "last": "", "prices": {}, "id": "", "barcode": "",
                        "url": "", "brand_col": "", "cat": "", "sub": "",
                    }
                p["first"] = min(p["first"], day)
                if day >= p["last"]:
                    p["last"], p["name"] = day, name
                if day in p["prices"]:
                    stats[store]["rows_same_day_repeat"] += 1
                p["prices"][day] = min(price, p["prices"].get(day, price))
                for field, cols in (("id", ID_COLS), ("barcode", BARCODE_COLS), ("url", URL_COLS),
                                    ("brand_col", BRAND_COLS)):
                    v = pick(r, cols)
                    if v:
                        p[field] = v
                cat, sub = pick(r, CAT_COLS), pick(r, SUB_COLS)
                if cat.isdigit() and cat != "0":
                    p["cat"] = cat.zfill(2)
                if re.fullmatch(r"\d{7}", sub):
                    p["sub"] = sub
        print(f"{store}: {stats[store]['files_read']} files, {stats[store]['rows_read']:,} rows", flush=True)

    store_last = defaultdict(str)
    for (store, _), p in products.items():
        store_last[store] = max(store_last[store], p["last"])

    out_rows = []
    for (store, key), p in sorted(products.items()):
        issues = []
        # Sizes are read from the folded name with its hyphens, so model codes stay whole.
        attrs = extract(re.sub(r"\s+", " ", fold(p["name"])))
        # A store's own brand column wins, spelled as in the brand list ("COLGATE" -> "Colgate").
        brand = (BRANDS.get(name_key(p["brand_col"]), p["brand_col"]) if p["brand_col"]
                 else find_brand(key, BRANDS))
        days = sorted(p["prices"])
        latest_price = p["prices"][days[-1]]
        real = [v for v in p["prices"].values() if v not in PLACEHOLDER_PRICES]
        if not brand:
            issues.append("brand_not_found")
        if not attrs["size_value"]:
            issues.append("size_not_found")
        if latest_price in PLACEHOLDER_PRICES:
            issues.append("price_placeholder_suspect")
        if real and max(real) > 5 * min(real):
            issues.append("price_range_suspect")
        if not p["sub"]:
            issues.append("tufe_item_missing")
        if p["last"] < store_last[store]:
            issues.append("not_in_latest_scrape")
        if not p["id"] and not p["barcode"]:
            issues.append("no_store_product_id")
        up, upu = unit_price(latest_price, attrs)
        core = {"brand_not_found", "size_not_found", "price_placeholder_suspect", "price_range_suspect"}
        out_rows.append({
            "retailer": store,
            "retailer_product_id": p["id"],
            "barcode": p["barcode"],
            "product_url": p["url"],
            "product_name": p["name"],
            "name_key": key,
            "brand": brand,
            **{k: attrs[k] for k in ("size_value", "size_unit", "pack_count", "sold_by")},
            **{k: attrs[k] for k in ("fat", "lactose_free", "organic", "flavour")},
            "price_latest_tl": f"{latest_price:.2f}",
            "unit_price_tl": up,
            "unit_price_unit": upu,
            "price_min_tl": f"{min(real):.2f}" if real else "",
            "price_max_tl": f"{max(real):.2f}" if real else "",
            "first_seen": p["first"],
            "last_seen": p["last"],
            "days_seen": len(days),
            "category_number": p["cat"],
            "sub_category_number": p["sub"],
            "status": "review" if core & set(issues) else "ok",
            "issues": ";".join(issues),
        })
        s = stats[store]
        s["products"] += 1
        s["products_ok"] += out_rows[-1]["status"] == "ok"
        s["in_latest_scrape"] += "not_in_latest_scrape" not in issues
        s["brand_found"] += bool(brand)
        s["size_found"] += bool(attrs["size_value"])
        s["unit_price"] += bool(up)
        s["has_store_id"] += bool(p["id"] or p["barcode"])
        s["has_url"] += bool(p["url"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "grocery_products.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    cols = ["files_read", "files_undated", "files_unreadable", "files_thousands_fixed", "rows_read",
            "rows_dropped_no_name_or_price", "rows_same_day_repeat", "products", "products_ok",
            "in_latest_scrape", "brand_found", "size_found", "unit_price", "has_store_id", "has_url"]
    with (OUT_DIR / "grocery_summary.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["retailer", "first_date", "last_date"] + cols)
        for store in sorted(stats):
            firsts = [p["first"] for (s, _), p in products.items() if s == store]
            w.writerow([store, min(firsts) if firsts else "", store_last.get(store, "")]
                       + [stats[store][c] for c in cols])
    total = Counter()
    for s in stats.values():
        total.update(s)
    print(f"products: {total['products']:,} ({total['products_ok']:,} ok) from {total['rows_read']:,} rows "
          f"in {total['files_read']:,} files -> {OUT_DIR}")


if __name__ == "__main__":
    main()
