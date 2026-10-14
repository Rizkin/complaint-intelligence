"""Entity matching v1: CFPB company name -> FDIC certificate (or "no bank").

Method
  1. Normalize names (case, '&', punctuation, legal suffixes, generic words).
  2. Score the CFPB name against every FDIC charter name AND every FDIC holding-company name (rapidfuzz).
  3. A holding-company hit resolves to the largest-asset charter of that holding company (the deposit-taking bank).
  4. Accept only if score >= THRESHOLD; otherwise the answer is "no bank" (credit unions, fintechs, collectors, bureaus).

Writes table main.entity_match (company, n_complaints, cert, institution, holding_company, state, assets_bn, score, match_type,
alt_candidates) and data/eval/entity_match.csv. Date-aware overrides (Discover merger) stay in the dbt seed, not here.

Usage: uv run python pipelines/entity_match.py [--threshold 88]
"""

import argparse
import json
import re

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process

LEGAL = {"INC", "INCORPORATED", "LLC", "LP", "LLP", "LTD", "CORP", "CORPORATION", "CO", "COMPANY", "THE", "NA", "PC", "PLC", "DBA",
         "OF", "AND"}
GENERIC = {"HOLDINGS", "HOLDING", "HOLDCO", "GROUP", "BANCORP", "BANCORPORATION", "BANCSHARES", "BCORP", "FINANCIAL", "SERVICES",
           "USA", "US", "BANK", "BANKS", "TRUST", "SAVINGS", "NATIONAL", "ASSOCIATION", "FSB", "SSB", "STATE"}
NATIONAL = [("NATIONAL ASSOCIATION", ""), ("N A", ""), ("N.A.", "")]


def norm(s, drop_generic=True):
    s = (s or "").upper().replace("&", " AND ")
    s = re.sub(r"\bN\.?\s?A\.?\b", " ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    toks = [t for t in s.split() if t not in LEGAL and not (drop_generic and t in GENERIC)]
    if not toks:  # name made only of generic words: keep them so it can still match itself
        toks = [t for t in s.split() if t not in LEGAL]
    return " ".join(toks)


def similarity(a, b, **kwargs):
    """Strict similarity: full-string and token-order-insensitive ratios only (no partial matching)."""
    return max(fuzz.ratio(a, b), fuzz.token_sort_ratio(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=90.0)
    ap.add_argument("--db", default="data/cfpb.duckdb")
    a = ap.parse_args()

    con = duckdb.connect(a.db)
    fdic = con.execute("""SELECT CERT, NAME, NAMEHCR, STALP, coalesce(ASSET, 0) AS ASSET, ACTIVE FROM fdic_all_institutions""").df()
    fdic["name_n"] = fdic.NAME.map(norm)
    fdic["hc_n"] = fdic.NAMEHCR.fillna("").map(norm)
    companies = con.execute("""SELECT company, count(*) AS n FROM analytics.fct_complaint GROUP BY 1 ORDER BY n DESC""").df()

    # choices: (normalized text, cert, kind). Holding-company choices resolve to the biggest charter of that HC.
    big_by_hc = (fdic[fdic.hc_n != ""].sort_values("ASSET", ascending=False).groupby("hc_n").head(1)
                 .set_index("hc_n")[["CERT", "NAME", "NAMEHCR", "STALP", "ASSET"]])
    choices, meta = [], []
    for r in fdic.itertuples():
        choices.append(r.name_n)
        meta.append(("charter", r.CERT))
    for hc, r in big_by_hc.iterrows():
        choices.append(hc)
        meta.append(("holding_company", int(r.CERT)))
    by_cert = fdic.set_index("CERT")

    out = []
    for c in companies.itertuples():
        q = norm(c.company)
        if not q:
            out.append((c.company, c.n, None, None, None, None, None, 0.0, "no_bank", "[]"))
            continue
        hits = process.extract(q, choices, scorer=similarity, limit=80, score_cutoff=60)
        # de-duplicate by cert, keep best score per cert
        seen, cands = set(), []
        for text, score, idx in hits:
            kind, cert = meta[idx]
            if cert in seen:
                continue
            seen.add(cert)
            cands.append((cert, kind, float(score)))
        alts = json.dumps([{"cert": int(k), "name": by_cert.loc[k, "NAME"], "kind": kd, "score": round(sc, 1)} for k, kd, sc in cands[:3]])
        if cands and cands[0][2] >= a.threshold:
            top = cands[0][2]
            tied = [x for x in cands if top - x[2] < 0.5]
            cert, kind, sc = max(tied, key=lambda x: (x[1] == "holding_company", float(by_cert.loc[x[0], "ASSET"])))  # tie: holding-company match first, then largest bank
            score = sc
            b = by_cert.loc[cert]
            out.append((c.company, c.n, int(cert), b.NAME, (b.NAMEHCR if pd.notna(b.NAMEHCR) and b.NAMEHCR else None), b.STALP, round(float(b.ASSET) / 1e6, 2) if pd.notna(b.ASSET) else None, round(score, 1), kind, alts))
        else:
            best = cands[0][2] if cands else 0.0
            out.append((c.company, c.n, None, None, None, None, None, round(best, 1), "no_bank", alts))

    res = pd.DataFrame(out, columns=["company", "n_complaints", "cert", "institution", "holding_company", "state", "assets_bn", "score",
                                     "match_type", "alt_candidates"])
    con.register("res_df", res)
    con.execute("CREATE OR REPLACE TABLE entity_match AS SELECT * FROM res_df")
    res.to_csv("data/eval/entity_match.csv", index=False)

    matched = res[res.cert.notna()]
    print(f"{len(res)} companies; matched {len(matched)} ({matched.n_complaints.sum() / res.n_complaints.sum():.1%} of complaints); "
          f"no-bank {len(res) - len(matched)}")
    print(matched.head(40)[["company", "institution", "cert", "score", "match_type"]].to_string(max_colwidth=42))

    # sanity check on what we already know (seed + exclusion list): not the evaluation, just a smoke test
    seed = con.execute("SELECT * FROM read_csv_auto('pipelines/dbt/seeds/entity_map_seed.csv')").df()
    seed = seed[seed.role.isin(["customer", "peer"])]
    excl = con.execute("SELECT * FROM read_csv_auto('pipelines/dbt/seeds/company_exclusions.csv')").df()
    r = res.set_index("company")
    ok = sum(int(r.loc[x.cfpb_company, "cert"] == x.fdic_cert) for x in seed.itertuples() if x.cfpb_company in r.index)
    print(f"\nsmoke test, known banks: {ok}/{len(seed)} correct cert")
    for x in seed.itertuples():
        if x.cfpb_company in r.index and r.loc[x.cfpb_company, "cert"] != x.fdic_cert:
            print("  MISS:", x.cfpb_company, "->", r.loc[x.cfpb_company, "cert"], r.loc[x.cfpb_company, "institution"], "| expected", x.fdic_cert)
    wrong_nb = [x.cfpb_company for x in excl.itertuples() if x.cfpb_company in r.index and pd.notna(r.loc[x.cfpb_company, "cert"])]
    print(f"smoke test, known non-banks: {len(excl) - len(wrong_nb)}/{len(excl)} correctly 'no bank'; false matches: {wrong_nb}")


if __name__ == "__main__":
    main()
