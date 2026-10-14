"""Entity matching v2: CFPB company name -> FDIC certificate (or "no bank"). Match means: the company IS or OWNS the FDIC bank.

v1 -> v2 changes (from the 100 human-verified pairs, docs/entity-matching-review.md)
  - candidates include charters ENDED since 2023-12-31 (merged/renamed banks that CFPB still files under)
  - v2.2 (post-hoc): 'National Association' is a charter suffix in exact-name comparison; name-only match accepted for banks with assets >= $5B
  - state conflict: a US state named in the CFPB name must match the bank's state (v2.1, added after the fresh-50 test; not yet re-tested)
  - stricter acceptance: a fuzzy hit is accepted only with name evidence, which stops non-banks from colliding with small banks
        reject if the CFPB name has a non-bank legal form (LLC/LP/LLP/PC) and no bank word
        accept if  raw name == charter name, or raw name == holding-company name,
                   or >= 2 distinctive tokens with a bank word / FINANCIAL,
                   or 1 distinctive token with a bank word and score >= 95
  - human-reviewed overrides (pipelines/dbt/seeds/entity_overrides.csv) win over the algorithm in the final table

Writes main.entity_match_core (algorithm only) and main.entity_match (overrides applied); CSVs in data/eval/.
Usage: uv run python pipelines/entity_match.py [--threshold 90]
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
BANKWORD = re.compile(r"\b(BANK|BANKS|BANKING|BANKERS|BANC\w*|BANCORP|BANCSHARES|BCORP|TRUST|SAVINGS)\b", re.I)
FINWORD = re.compile(r"\bFINANCIAL\b", re.I)
LARGE_BANK_BN = 5.0  # $5B: a name-only match to a bank this size is plausible; tiny look-alikes (Devon, Halstead) are not
NONBANK_FORM = re.compile(r"\b(LLC|L\.L\.C\.|LP|L\.P\.|LLP|P\.C\.|PLLC)\b", re.I)


CHARTER_SUFFIX = {"NATIONAL", "ASSOCIATION"}


def norm(s, drop_generic=True):
    s = (s or "").upper().replace("&", " AND ")
    s = re.sub(r"\bN\.?\s?A\.?\b", " ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    toks = [t for t in s.split() if t not in LEGAL and not (drop_generic and t in GENERIC) and (drop_generic or t not in CHARTER_SUFFIX)]
    if not toks:
        toks = [t for t in s.split() if t not in LEGAL]
    return " ".join(toks)


def similarity(a, b, **kwargs):
    return max(fuzz.ratio(a, b), fuzz.token_sort_ratio(a, b))


STATES = {"ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT",
          "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
          "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI",
          "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH",
          "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
          "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN",
          "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WEST VIRGINIA": "WV", "WASHINGTON": "WA", "WISCONSIN": "WI",
          "WYOMING": "WY", "PUERTO RICO": "PR"}


def named_states(company):
    """State abbreviations whose full names appear in the company name (longest names first so 'WEST VIRGINIA' hides 'VIRGINIA')."""
    text, found = company.upper(), set()
    for name in sorted(STATES, key=len, reverse=True):
        if re.search(rf"\b{name}\b", text):
            found.add(STATES[name])
            text = re.sub(rf"\b{name}\b", " ", text)
    return found


def accept(company, score, cand, thr):
    """Return (accepted, reason). cand has name, hc, kind."""
    if score < thr:
        return False, "below_threshold"
    raw = norm(company, drop_generic=False)
    toks = norm(company).split()
    bank = bool(BANKWORD.search(company))
    fin = bool(FINWORD.search(company))
    if NONBANK_FORM.search(company) and not bank:
        return False, "nonbank_legal_form"
    named = named_states(company)
    if named and cand.get("state") and cand["state"] not in named and raw != norm(cand["name"], drop_generic=False):
        return False, "state_conflict"
    if raw == norm(cand["name"], drop_generic=False):
        return True, "raw_equals_charter"
    if cand["hc"] and raw == norm(cand["hc"], drop_generic=False):
        return True, "raw_equals_holding_company"
    if len(toks) >= 2 and (bank or fin):
        return True, "two_tokens_with_bank_or_financial"
    if len(toks) == 1 and bank and score >= 95:
        return True, "one_token_with_bank_word"
    if score >= 95 and (cand.get("assets_bn") or 0) >= LARGE_BANK_BN:
        return True, "large_bank_name_match"
    return False, "insufficient_name_evidence"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=90.0)
    ap.add_argument("--db", default="data/cfpb.duckdb")
    a = ap.parse_args()

    con = duckdb.connect(a.db)
    fdic = con.execute("""SELECT CERT, NAME, NAMEHCR, STALP, coalesce(ASSET, 0) AS ASSET, ACTIVE, ENDEFYMD FROM fdic_all_institutions""").df()
    fdic["name_n"] = fdic.NAME.map(norm)
    fdic["hc_n"] = fdic.NAMEHCR.fillna("").map(norm)
    companies = con.execute("""SELECT company, count(*) AS n FROM analytics.fct_complaint GROUP BY 1 ORDER BY n DESC""").df()

    big_by_hc = (fdic[fdic.hc_n != ""].sort_values(["ACTIVE", "ASSET"], ascending=False).groupby("hc_n").head(1).set_index("hc_n"))
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
        base = dict(company=c.company, n_complaints=c.n, cert=None, institution=None, holding_company=None, state=None, assets_bn=None,
                    active=None, ended=None, score=0.0, match_type="no_bank", reason="no_candidates", alt_candidates="[]")
        if not q:
            out.append(base)
            continue
        hits = process.extract(q, choices, scorer=similarity, limit=80, score_cutoff=60)
        seen, cands = set(), []
        for text, score, idx in hits:
            kind, cert = meta[idx]
            if cert in seen:
                continue
            seen.add(cert)
            cands.append((cert, kind, float(score)))
        base["alt_candidates"] = json.dumps([{"cert": int(k), "name": by_cert.loc[k, "NAME"], "kind": kd, "score": round(sc, 1)}
                                              for k, kd, sc in cands[:3]])
        if not cands:
            out.append(base)
            continue
        top = cands[0][2]
        tied = [x for x in cands if top - x[2] < 0.5]
        # tie-break: holding-company hit, then active charter, then largest bank
        cert, kind, sc = max(tied, key=lambda x: (x[1] == "holding_company", int(by_cert.loc[x[0], "ACTIVE"]), float(by_cert.loc[x[0], "ASSET"])))
        b = by_cert.loc[cert]
        ok, reason = accept(c.company, sc, {"name": b.NAME, "hc": b.NAMEHCR if pd.notna(b.NAMEHCR) else "", "state": b.STALP, "assets_bn": float(b.ASSET) / 1e6}, a.threshold)
        base.update(score=round(sc, 1), reason=reason)
        if ok:
            base.update(cert=int(cert), institution=b.NAME, holding_company=(b.NAMEHCR if pd.notna(b.NAMEHCR) and b.NAMEHCR else None),
                        state=b.STALP, assets_bn=round(float(b.ASSET) / 1e6, 2), active=int(b.ACTIVE),
                        ended=(b.ENDEFYMD if int(b.ACTIVE) == 0 else None), match_type=kind)
        out.append(base)

    core = pd.DataFrame(out)
    # overrides: human review beats the algorithm. For companies with several dated rows use the one valid today (valid_to = far future).
    ov = pd.read_csv("pipelines/dbt/seeds/entity_overrides.csv")
    ov["valid_from"] = pd.to_datetime(ov.valid_from)
    ov = ov.sort_values(["cfpb_company", "valid_from"]).groupby("cfpb_company").tail(1).set_index("cfpb_company")
    final = core.copy()
    n_ov = 0
    for i, r in final.iterrows():
        if r.company in ov.index:
            o = ov.loc[r.company]
            n_ov += 1
            if pd.isna(o.fdic_cert):
                final.loc[i, ["cert", "institution", "holding_company", "state", "assets_bn", "active", "ended"]] = None
                final.loc[i, "match_type"], final.loc[i, "reason"] = "no_bank", "override_no_bank"
            else:
                b = by_cert.loc[int(o.fdic_cert)]
                final.loc[i, "cert"] = int(o.fdic_cert)
                final.loc[i, "institution"], final.loc[i, "state"] = b.NAME, b.STALP
                final.loc[i, "holding_company"] = b.NAMEHCR if pd.notna(b.NAMEHCR) and b.NAMEHCR else None
                final.loc[i, "assets_bn"] = round(float(b.ASSET) / 1e6, 2)
                final.loc[i, "active"], final.loc[i, "ended"] = int(b.ACTIVE), (b.ENDEFYMD if int(b.ACTIVE) == 0 else None)
                final.loc[i, "match_type"], final.loc[i, "reason"] = "override_" + o.relation, "override"

    for name, df in (("entity_match_core", core), ("entity_match", final)):
        con.register("tmp_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
        con.unregister("tmp_df")
        df.to_csv(f"data/eval/{name}.csv", index=False)
    for name, df in (("core (algorithm only)", core), ("final (with overrides)", final)):
        m = df[df.cert.notna()]
        print(f"{name}: {len(df)} companies; matched {len(m)} ({m.n_complaints.sum() / df.n_complaints.sum():.1%} of complaints); overrides applied {n_ov}")
    print(core.reason.value_counts().to_string())


if __name__ == "__main__":
    main()
