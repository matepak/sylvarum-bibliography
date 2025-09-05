# Projekt Sylvarum – Bibliografia (CSL JSON → BibTeX w CI)

- Źródło prawdy: `refs/bibliografia.json` (eksport z Zotero Group).
- `.bib` generowany automatycznie w CI (artefakt) lub lokalnie skryptem.

## Workflow

1. Edycja w Zotero Group → auto-eksport do `refs/bibliografia.json`.
2. Commit & push JSON.
3. GitHub Actions: walidacja + konwersja do BibTeX → artefakt `generated/bibliografia.bib`.

## Lokalnie:

```bash
python3 scripts/validate_json.py refs/bibliografia.json
scripts/convert_to_bib.sh                  # generuje generated/bibliografia.bib
python3 scripts/generate_citekeys.py \     # (opcjonalnie) stabilne klucze
  --in generated/bibliografia.bib --out generated/bibliografia.bib
```
