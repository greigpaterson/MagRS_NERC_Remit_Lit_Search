#!/usr/bin/env python3
"""
Reproduce publication counts for FORC, magnetic hysteresis and FMR studies
(1991-2025) from OpenAlex, split into: all, NERC-remit (keyword proxy), and
NERC-funded (OpenAlex funder F4320334631).

Standard library only. Usage:
    export OPENALEX_API_KEY=...        # optional but recommended (free key)
    python3 openalex_counts.py                 # per-year counts -> CSV
    python3 openalex_counts.py --dump-ids      # also save every matching work ID

Outputs (in --outdir, default ./results_<UTC date>):
    by_year.csv       technique,subset,year,count
    summary.csv       totals and 5-year bins
    queries.json      exact filter strings + request URLs + timestamp
    ids_<tech>_<subset>.txt   (with --dump-ids) OpenAlex work IDs, one per line
"""
import argparse, csv, datetime as dt, json, os, time, urllib.parse, urllib.request

API = "https://api.openalex.org/works"
NERC_FUNDER = "F4320334631"  # "Natural Environment Research Council" (GB)
YEARS = (1991, 2025)

# Technique definitions: OpenAlex title_and_abstract.search boolean expressions.
# Quoted phrases are matched as stemmed phrases; hyphens are tokenised, so
# "first order reversal curve" also matches "first-order reversal curves".
TECHNIQUES = {
    "FORC": '"first order reversal curve" OR "FORC diagram" OR "FORC distribution"',
    "Hysteresis": "hysteresis AND (magnetic OR magnetization OR magnetisation)",
    "FMR": '"ferromagnetic resonance"',
}

# NERC-remit proxy: co-occurrence with earth/environmental-science terms.
REMIT_TERMS = (
    'paleomagnetism OR palaeomagnetism OR paleomagnetic OR palaeomagnetic OR '
    '"rock magnetic" OR "rock magnetism" OR "environmental magnetism" OR '
    '"mineral magnetism" OR geomagnetic OR sediment OR soil OR rock OR basalt OR '
    'biomagnetism OR biogeomagnetism OR magnetotactic OR geological OR loess OR volcanic OR marine OR '
    'lake OR atmospheric OR pollution OR dust OR particulate'
)


def build_filter(tech_expr, subset):
    parts = [f"title_and_abstract.search:{tech_expr}",
             f"publication_year:{YEARS[0]}-{YEARS[1]}"]
    if subset == "remit":
        parts.append(f"title_and_abstract.search:{REMIT_TERMS}")
    elif subset == "nerc_funded":
        parts.append(f"funders.id:{NERC_FUNDER}")
    return ",".join(parts)


def get(params, api_key, retries=5):
    if api_key:
        params = {**params, "api_key": api_key}
    url = API + "?" + urllib.parse.urlencode(params, safe=":,|()\"")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "openalex-counts/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), url
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep(2 ** i); continue
            raise SystemExit(f"HTTP {e.code} for {url}\n{e.read()[:500]!r}")


def year_counts(flt, api_key):
    data, url = get({"filter": flt, "group_by": "publication_year"}, api_key)
    counts = {int(g["key"]): g["count"] for g in data["group_by"]}
    return {y: counts.get(y, 0) for y in range(YEARS[0], YEARS[1] + 1)}, data["meta"]["count"], url


def dump_ids(flt, path, api_key):
    cursor, n = "*", 0
    with open(path, "w") as f:
        while cursor:
            data, _ = get({"filter": flt, "select": "id,publication_year,doi",
                           "per-page": 200, "cursor": cursor}, api_key)
            for w in data["results"]:
                f.write(f'{w["id"]}\t{w["publication_year"]}\t{w.get("doi") or ""}\n'); n += 1
            cursor = data["meta"].get("next_cursor")
            if not data["results"]:
                break
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=f"results_{dt.date.today().isoformat()}")
    ap.add_argument("--dump-ids", action="store_true")
    a = ap.parse_args()
    key = os.environ.get("OPENALEX_API_KEY")
    os.makedirs(a.outdir, exist_ok=True)

    log = {"retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "years": YEARS,
           "nerc_funder_id": NERC_FUNDER, "queries": []}
    rows, summary = [], []
    for tech, expr in TECHNIQUES.items():
        for subset in ("all", "remit", "nerc_funded"):
            flt = build_filter(expr, subset)
            by_year, total, url = year_counts(flt, key)
            assert sum(by_year.values()) == total, (tech, subset)
            rows += [[tech, subset, y, c] for y, c in by_year.items()]
            bins = [sum(by_year[y] for y in range(s, s + 5)) for s in range(YEARS[0], YEARS[1]+1, 5)]
            summary.append([tech, subset, total, *bins])
            entry = {"technique": tech, "subset": subset, "filter": flt,
                     "url": url.replace(f"&api_key={key}", "") if key else url, "total": total}
            if a.dump_ids:
                entry["ids_file"] = f"ids_{tech}_{subset}.txt"
                entry["ids_dumped"] = dump_ids(flt, os.path.join(a.outdir, entry["ids_file"]), key)
            log["queries"].append(entry)
            print(f"{tech:11s} {subset:12s} {total:6d}")

    with open(os.path.join(a.outdir, "by_year.csv"), "w", newline="") as f:
        csv.writer(f).writerows([["technique", "subset", "year", "count"], *rows])
    with open(os.path.join(a.outdir, "summary.csv"), "w", newline="") as f:
        csv.writer(f).writerows([["technique", "subset", "total_1991_2025", "1991-95",
                                  "1996-00", "2001-05", "2006-10", "2011-15", "2016-20",
                                  "2021-25"], *summary])
    with open(os.path.join(a.outdir, "queries.json"), "w") as f:
        json.dump(log, f, indent=2)


if __name__ == "__main__":
    main()
