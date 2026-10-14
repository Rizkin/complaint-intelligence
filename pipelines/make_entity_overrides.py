"""Write human-reviewed entity overrides (CFPB company -> FDIC cert, or none) to a dbt seed.

Match definition: the CFPB company IS an FDIC-insured bank or OWNS one (holding company / direct bank subsidiary).
Partner-bank relationships (fintech -> sponsor bank) are NOT matches; they are listed in docs/entity-matching-review.md.
Source of every row: human review in chat, 2026-10-15 (plus FDIC BankFind for certs and merger dates).

Usage: uv run python pipelines/make_entity_overrides.py
"""

import duckdb
import pandas as pd

EPOCH = "2011-12-01"
FAR = "9999-12-31"
# (exact CFPB company, cert or None, valid_from, valid_to, relation, note)
ROWS = [
    # merged charters: CFPB keeps the old name (same pattern as Discover Bank -> Capital One, docs/01-data-quality.md #12)
    ("Synovus Bank", 873, EPOCH, "2026-01-02", "is_bank", "Synovus Bank (GA) merged 2026-01-02"),
    ("Comerica", 983, EPOCH, "2026-02-01", "is_bank", "Comerica Bank (TX) charter ended 2026-02-01"),
    ("WEBSTER BANK, NATIONAL ASSOCIATION", 18221, EPOCH, "2026-08-20", "is_bank", "Webster Bank N.A. charter ended 2026-08-20"),
    ("SANDY SPRING BANCORP, INC.", 4865, EPOCH, "2025-04-01", "owns_bank", "Sandy Spring Bank charter ended 2025-04-01"),
    ("PACIFIC PREMIER BANCORP, INC.", 32172, EPOCH, "2025-09-01", "owns_bank", "Pacific Premier Bank N.A. charter ended 2025-09-01"),
    ("HSBC NORTH AMERICA HOLDINGS INC.", 57890, EPOCH, FAR, "owns_bank", "HSBC Bank USA, N.A."),
    ("Bread Financial Holdings, Inc.", 57570, EPOCH, FAR, "owns_bank", "Comenity Capital Bank; FDIC lists no holding company for it"),
    ("PINNACLE FINANCIAL PARTNERS, INC.", 35583, EPOCH, FAR, "owns_bank", "Pinnacle Bank (TN)"),
    ("SEACOAST BANKING CORPORATION OF FLORIDA", 131, EPOCH, FAR, "owns_bank", "Seacoast National Bank"),
    ("DIME COMMUNITY BANCSHARES, INC.", 6976, EPOCH, FAR, "owns_bank", "Dime Commercial Bank after the 2026 rebrand (human); earlier charter history unverified"),
    ("Block, Inc.", 59177, EPOCH, FAR, "owns_bank", "Square Financial Services (ILC subsidiary). Cash App complaints are mostly NOT about this bank; do not use for complaints-per-assets"),
    ("CITY NATIONAL BANK", 17281, EPOCH, FAR, "is_bank", "assumed City National Bank (CA); the WV bank 17735 is a different, small bank. Ambiguous (36 complaints)"),
    ("Washington Trust Bank Financial Corporation", 1281, EPOCH, FAR, "owns_bank", "Spokane WA bank per human review; not Westerly RI 23623"),
    # name collisions and non-bank affiliates: no FDIC bank
    ("MORGAN STANLEY & CO. LLC", None, EPOCH, FAR, "none", "broker-dealer sister of Morgan Stanley Bank N.A., not the bank or its owner"),
    ("Halsted Financial Services, LLC.", None, EPOCH, FAR, "none", "debt collector; name collision with Halstead Bank"),
    ("Bridge IT, Inc.", None, EPOCH, FAR, "none", "fintech (Brigit); name collision with Bridge City State Bank"),
    ("Lincoln Financial Services", None, EPOCH, FAR, "none", "insurer (Lincoln National); name collision with Lincoln Savings Bank"),
    ("HEARTLAND FINANCIAL USA, INC.", None, EPOCH, FAR, "none", "multi-bank holding acquired by UMB (2025); not HBT's Heartland Bank and Trust; low volume, unresolved"),
    ("INDEPENDENT BANK GROUP, INC.", 33555, "2025-01-01", FAR, "owns_bank", "acquired by SouthState 2025-01-01; Independent Bank merged into SouthState Bank N.A.; test row 69"),
    ("NEW YORK COMMUNITY BANCORP INC", 32541, EPOCH, FAR, "owns_bank", "renamed Flagstar Financial (Oct 2024); Flagstar Bank N.A.; test row 72"),
    ("First Credit Corporation", None, EPOCH, FAR, "none", "name collision with First Credit Bank; test row 55"),
    ("Devon Financial Services, Inc.", None, EPOCH, FAR, "none", "Illinois consumer/title-loan company, not Devon Bank; test row 61"),
    ("People Trust", None, EPOCH, FAR, "none", "nonprofit CDFI with a former credit-union sponsorship (NCUA), not Peoples Bank; test row 75"),
    ("CADENCE BANK", 11813, EPOCH, "2026-02-01", "is_bank", "Cadence Bank (MS) merged into Huntington 2026-02-01; test row 89"),
    ("CADENCE BANK", 6560, "2026-02-01", FAR, "is_bank", "successor: The Huntington National Bank; test row 89"),
    ("BMW Financial Services NA, LLC", 35141, EPOCH, FAR, "owns_bank", "BMW Bank of North America is its direct subsidiary; test row 98"),
    ("River Financial Inc.", None, EPOCH, FAR, "none", "Bitcoin fintech; not River Financial Corp (AL) which owns River Bank & Trust; fresh-50 row 7"),
    ("First Bancorp North Carolina", 15019, EPOCH, FAR, "owns_bank", "First Bank (NC); fresh-50 row 43"),
    # test-sheet rows judged wrong by the human
    ("Barker Financial LLC", None, EPOCH, FAR, "none", "test row 7"),
    ("National Commercial Services, Inc", None, EPOCH, FAR, "none", "test row 25"),
    ("United Shore Financial Services, LLC", None, EPOCH, FAR, "none", "mortgage lender; test row 32"),
    ("Clayton Holdings LLC", None, EPOCH, FAR, "none", "test row 42"),
    ("AMERIFIRST FINANCIAL, INC.", None, EPOCH, FAR, "none", "mortgage lender, not AmeriFirst Bank (AL); test row 44"),
]

con = duckdb.connect("data/cfpb.duckdb", read_only=True)
known = set(con.execute("SELECT company FROM entity_match").df().company)
missing = [r[0] for r in ROWS if r[0] not in known]
if missing:
    raise SystemExit(f"company names not found in entity_match: {missing}")
df = pd.DataFrame(ROWS, columns=["cfpb_company", "fdic_cert", "valid_from", "valid_to", "relation", "note"])
df["source"] = "human review 2026-10-15"
df.to_csv("pipelines/dbt/seeds/entity_overrides.csv", index=False)
print(f"wrote {len(df)} overrides ({int(df.fdic_cert.notna().sum())} to a bank, {int(df.fdic_cert.isna().sum())} no-bank)")
