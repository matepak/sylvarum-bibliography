#!/usr/bin/env python3
import sys, re
from collections import Counter
try:
    import bibtexparser
except ImportError:
    print("ERROR: missing bibtexparser. Install with: pip install bibtexparser")
    sys.exit(2)

REQ_FIELDS = {
    "article": {"title", "author", "journal", "year"},
    "inproceedings": {"title", "author", "booktitle", "year"},
    "book": {"title", "year"},
    "incollection": {"title", "booktitle", "year"},
    "phdthesis": {"title", "author", "school", "year"},
    "mastersthesis": {"title", "author", "school", "year"},
    "misc": {"title"},
    "techreport": {"title", "institution", "year"},
}

ASCII_KEY = re.compile(r'^[A-Za-z0-9:_-]+$')
YEAR_RE = re.compile(r'^\d{4}$')

def main(path):
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)

    entries = db.entries
    keys = [e.get("ID","").strip() for e in entries]
    dup = [k for k,c in Counter(keys).items() if c>1 and k]
    errors = []

    if dup:
        errors.append(f"Duplicate citekeys: {dup}")

    for e in entries:
        key = e.get("ID","").strip()
        if not key:
            errors.append("Entry without citekey (ID)")
            continue
        if not ASCII_KEY.match(key):
            errors.append(f"Non-ASCII or invalid chars in key: {key}")

        etype = e.get("ENTRYTYPE","").lower()
        req = REQ_FIELDS.get(etype, {"title","year"})
        missing = [f for f in req if not e.get(f)]
        if missing:
            errors.append(f"{key}: missing fields for {etype}: {missing}")

        year = (e.get("year") or "").strip()
        if year and not YEAR_RE.match(year):
            errors.append(f"{key}: invalid year `{year}` (expected YYYY)")

    if errors:
        print("BIB validation FAILED:")
        for i, err in enumerate(errors, 1):
            print(f" {i}. {err}")
        sys.exit(1)
    else:
        print(f"BIB validation OK ({len(entries)} entries).")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_bib.py refs/bibliografia.bib")
        sys.exit(2)
    main(sys.argv[1])
