"""
Week 1 dataset audit for Team 1.

Reads the raw daily files and the spec files and writes, into data/audit/:

    field_inventory.csv    one row per store and field: type, missing, distinct, example
    schema_summary.csv     one row per store: columns, schema group, required columns, price format
    electronics_quality_stats.csv
                           one row per electronics store and check
    summary.json           the numbers the reports quote

Nothing is changed in the source files. Run:

    python scrapers/audit/build_week1_audit.py --datas <InflationItems/Datas>
        [--specs data/specs] [--clean data/specs_clean]
        [--stores data/groceries/pricematch/stores]
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

csv.field_size_limit(10**9)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "audit"
REQUIRED = ("product_name", "price", "category_number", "sub_category_number")
MISSING = {"", "nan", "none", "null", "n/a", "na", "-"}
SNAPSHOT_END = "2026-10-29"
ELECTRONICS_DAILY = {
    "Beymen": ("08_Communication/Beymen", r"^beymen_(\d{4}-\d{2}-\d{2})\.csv$"),
    "Pozitif": ("08_Communication/PozitifTeknoloji", r"^pozitifTeknoloji_(\d{4}-\d{2}-\d{2})\.csv$"),
    "Samsung": ("08_Communication/Samsung", r"^samsung_(\d{4}-\d{2}-\d{2})\.csv$"),
}
ELECTRONICS_ID_FIELDS = ("UrunID", "product_id", "id", "sku", "model_code", "modelCode")

PATTERNS = [
    ("integer", re.compile(r"^-?\d+$")),
    ("decimal", re.compile(r"^-?\d+\.\d+$")),
    ("date", re.compile(r"^\d{4}-\d{2}-\d{2}([ T].*)?$")),
    ("url", re.compile(r"^https?://", re.I)),
    ("boolean", re.compile(r"^(true|false)$", re.I)),
    ("json", re.compile(r"^[\[{].*[\]}]$", re.S)),
]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows, bad = [], 0
        for raw in reader:
            if not raw:
                continue
            if len(raw) != len(header):
                bad += 1
            rows.append(dict(zip(header, raw)))
    return header, rows, bad


def is_missing(value):
    return value is None or value.strip().lower() in MISSING


def value_type(value):
    for name, pattern in PATTERNS:
        if pattern.match(value.strip()):
            return name
    return "text"


def field_type(values):
    counts = Counter(value_type(v) for v in values)
    if not counts:
        return "empty"
    if set(counts) == {"integer", "decimal"}:
        return "decimal"
    total = sum(counts.values())
    main, n = counts.most_common(1)[0]
    return main if n == total else f"mixed ({main} {n / total:.0%})"


def price_format(value):
    v = value.strip()
    if re.fullmatch(r"\d+(\.\d+)?", v):
        return "plain_number"
    if re.fullmatch(r"\d+,\d{1,2}", v):
        return "decimal_comma"
    if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d{1,2}", v):
        return "thousand_dot_decimal_comma"
    if re.search(r"₺|TL", v, re.I):
        return "with_currency_text"
    if re.fullmatch(r"-\d+(\.\d+)?", v):
        return "negative"
    return "other" if v else "empty"


def to_price(value):
    v = value.strip()
    if re.fullmatch(r"\d+(\.\d+)?", v):
        return float(v)
    if re.fullmatch(r"\d+,\d{1,2}", v):
        return float(v.replace(",", "."))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d{1,2}", v):
        return float(v.replace(".", "").replace(",", "."))
    return None


def inventory(group, store, path, date, header, rows):
    out = []
    for field in header:
        values = [r.get(field) or "" for r in rows]
        present = [v for v in values if not is_missing(v)]
        out.append({
            "source_group": group, "store": store, "file": path.name, "date": date, "field": field,
            "inferred_type": field_type(present), "rows": len(rows),
            "missing": len(rows) - len(present),
            "missing_pct": round(100 * (len(rows) - len(present)) / len(rows), 2) if rows else 0,
            "distinct": len(set(present)),
            "example": present[0].replace("\n", " ")[:80] if present else "",
        })
    return out


def schema_row(group, store, path, date, header, rows, bad):
    name_field = "product_name" if "product_name" in header else ("name" if "name" in header else None)
    prices = [r.get("price") or "" for r in rows] if "price" in header else []
    formats = Counter(price_format(p) for p in prices)
    names = [r.get(name_field) or "" for r in rows] if name_field else []
    seen, exact, by_name = Counter(), 0, defaultdict(set)
    for r in rows:
        key = ((r.get(name_field) or "").strip(), (r.get("price") or "").strip())
        exact += seen[key] > 0
        seen[key] += 1
        by_name[key[0]].add(key[1])
    return {
        "source_group": group, "store": store, "file": path.name, "date": date, "rows": len(rows),
        "columns": len(header), "header": "|".join(header),
        "has_all_required": all(c in header for c in REQUIRED),
        "missing_required": "|".join(c for c in REQUIRED if c not in header),
        "extra_columns": "|".join(c for c in header if c not in REQUIRED),
        "wrong_column_count_rows": bad,
        "empty_name": sum(is_missing(n) for n in names),
        "empty_price": sum(is_missing(p) for p in prices),
        "unusable_price": sum(1 for p in prices if not is_missing(p) and (to_price(p) is None or to_price(p) <= 0)),
        "exact_duplicates": exact if prices else "",
        "names_with_several_prices": sum(1 for n, ps in by_name.items() if n and len(ps) > 1) if prices else "",
        "price_formats": "; ".join(f"{k}={v}" for k, v in formats.most_common()),
        "category_number_lengths": lengths(rows, "category_number"),
        "sub_category_lengths": lengths(rows, "sub_category_number"),
        "sub_category_zero": sum(1 for r in rows if (r.get("sub_category_number") or "").strip() == "0"),
    }


def lengths(rows, field):
    counts = Counter(len((r.get(field) or "").strip()) for r in rows if field in r)
    return "; ".join(f"{k}={v}" for k, v in sorted(counts.items()))


def grocery_sources(datas, stores_dir):
    for path in sorted(stores_dir.glob("*.csv")):
        with open(path, newline="", encoding="utf-8-sig") as f:
            first = next(csv.DictReader(f))
        folder = first["retailer"]
        yield folder, datas / "01_Food" / folder / first["source_file"], first["scrape_date"]


def newest_daily(datas, folder, pattern):
    best = None
    for path in (datas / folder).iterdir():
        match = re.match(pattern, path.name)
        if match and match.group(1) <= SNAPSHOT_END and (best is None or match.group(1) > best[0]):
            best = (match.group(1), path)
    return best


def electronics_checks(store, spec_path, clean_path, daily):
    header, rows, bad = read_csv(spec_path)
    _, clean, _ = read_csv(clean_path)
    ids = Counter(r["retailer_product_id"] for r in rows)
    names = Counter(r["name"].strip() for r in rows)
    models = defaultdict(set)
    for r in rows:
        if r["model_code"].strip():
            models[r["model_code"].strip()].add(r["retailer_product_id"])

    def count(test):
        return sum(1 for r in rows if test(r))

    def bad_number(field):
        return count(lambda r: r[field].strip() and not re.fullmatch(r"\d+(\.\d+)?", r[field].strip()))

    date = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    checks = {
        "rows": len(rows),
        "wrong_column_count_rows": bad,
        "empty_name": count(lambda r: is_missing(r["name"])),
        "empty_retailer_product_id": count(lambda r: is_missing(r["retailer_product_id"])),
        "repeated_retailer_product_id": sum(c - 1 for c in ids.values() if c > 1),
        "repeated_name_rows": sum(c - 1 for c in names.values() if c > 1),
        "model_code_on_several_ids": sum(1 for v in models.values() if len(v) > 1),
        "bad_storage_gb": bad_number("storage_gb"),
        "bad_ram_gb": bad_number("ram_gb"),
        "bad_screen_size_in": bad_number("screen_size_in"),
        "bad_url": count(lambda r: r["url"].strip() and not r["url"].startswith("http")),
        "bad_date": count(lambda r: not date.match(r["first_seen"]) or not date.match(r["last_seen"])),
        "first_seen_after_last_seen": count(lambda r: r["first_seen"] > r["last_seen"]),
        "condition_not_new": count(lambda r: r["condition"] != "new"),
        "bundles": count(lambda r: r["is_bundle"].strip().lower() == "true"),
        "clean_rows": len(clean),
        "clean_needs_review": sum(1 for r in clean if r["data_quality_status"] != "clean"),
        "clean_no_brand": sum(1 for r in clean if not r["brand"].strip()),
        "clean_no_cpi_category": sum(1 for r in clean if not r["category"].strip()),
    }
    for field in ("brand", "model_code", "color", "storage_gb", "ram_gb", "screen_size_in", "capacity",
                  "category", "url", "image_url"):
        checks[f"missing_{field}"] = count(lambda r: is_missing(r[field]))

    d_header, d_rows, _ = read_csv(daily[1])
    prices = [r.get("price") or "" for r in d_rows]
    checks.update({
        "daily_file": daily[1].name, "daily_rows": len(d_rows),
        "daily_header": "|".join(d_header),
        "daily_empty_price": sum(is_missing(p) for p in prices),
        "daily_zero_or_bad_price": sum(1 for p in prices if not is_missing(p) and (to_price(p) is None or to_price(p) <= 0)),
    })
    best = (0, "", 0)
    for field in ELECTRONICS_ID_FIELDS:
        if field in d_header:
            with_id = [r for r in d_rows if (r.get(field) or "").strip()]
            joined = sum(1 for r in with_id if r[field].strip() in ids)
            if joined > best[0]:
                best = (joined, field, len(with_id))
    checks["daily_id_field"], checks["daily_rows_with_id"], checks["daily_rows_joined_to_spec"] = best[1], best[2], best[0]
    return checks


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datas", type=Path, required=True)
    parser.add_argument("--specs", type=Path, default=REPO_ROOT / "data" / "specs")
    parser.add_argument("--clean", type=Path, default=REPO_ROOT / "data" / "specs_clean")
    parser.add_argument("--stores", type=Path, default=REPO_ROOT / "data" / "groceries" / "pricematch" / "stores")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    fields, schemas = [], []
    for store, path, date in grocery_sources(args.datas, args.stores):
        header, rows, bad = read_csv(path)
        fields += inventory("grocery_daily", store, path, date, header, rows)
        schemas.append(schema_row("grocery_daily", store, path, date, header, rows, bad))

    stats, electronics = [], {}
    for store, (folder, pattern) in ELECTRONICS_DAILY.items():
        daily = newest_daily(args.datas, folder, pattern)
        if daily is None:
            raise SystemExit(f"no daily file found for {store}")
        header, rows, bad = read_csv(daily[1])
        fields += inventory("electronics_daily", store, daily[1], daily[0], header, rows)
        schemas.append(schema_row("electronics_daily", store, daily[1], daily[0], header, rows, bad))
        checks = electronics_checks(store, args.specs / f"{store.lower()}_specs.csv",
                                    args.clean / f"{store.lower()}_specs_clean.csv", daily)
        electronics[store] = checks
        stats += [{"store": store, "check": k, "value": v} for k, v in checks.items()]

    for spec in sorted(args.specs.glob("*_specs.csv")):
        header, rows, bad = read_csv(spec)
        store = spec.stem.replace("_specs", "")
        last = max((r.get("last_seen") or "" for r in rows), default="")
        fields += inventory("spec_file", store, spec, last, header, rows)
        schemas.append(schema_row("spec_file", store, spec, last, header, rows, bad))

    groups = {}
    for row in schemas:
        groups.setdefault(row["header"], f"S{len(groups) + 1:02d}")
        row["schema_group"] = groups[row["header"]]

    write_csv(OUT / "field_inventory.csv", fields, list(fields[0]))
    write_csv(OUT / "schema_summary.csv", schemas, list(schemas[0]))
    write_csv(OUT / "electronics_quality_stats.csv", stats, ["store", "check", "value"])
    summary = {
        "grocery_raw_rows": sum(r["rows"] for r in schemas if r["source_group"] == "grocery_daily"),
        "groups": {v: {"header": k, "stores": [r["store"] for r in schemas if r["header"] == k]}
                   for k, v in groups.items()},
        "stores": [{k: r[k] for k in ("source_group", "store", "date", "rows", "columns", "schema_group",
                                      "missing_required", "wrong_column_count_rows", "empty_name",
                                      "empty_price", "unusable_price", "exact_duplicates",
                                      "names_with_several_prices", "price_formats",
                                      "category_number_lengths", "sub_category_lengths",
                                      "sub_category_zero")} for r in schemas],
        "electronics": electronics,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
