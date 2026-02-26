#!/usr/bin/env python3
"""
zotero_sync.py — Sync Zotero group → refs/bibliography.bib → GitHub

Użycie:
  python3 zotero_sync.py            # eksport + walidacja + commit + push
  python3 zotero_sync.py --dry-run  # tylko eksport i walidacja, bez commita
  python3 zotero_sync.py --export-only  # tylko eksport do pliku
"""

import json
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from pyzotero import zotero

# Ścieżki
WORKSPACE = Path(__file__).parent.parent
CREDS_PATH = WORKSPACE / "memory" / "zotero.json"
BIB_PATH = WORKSPACE / "refs" / "bibliography.bib"
VALIDATE_SCRIPT = WORKSPACE / "scripts" / "validate_bib.py"
PYTHON = "/home/mateusz/miniconda3/bin/python3"


def load_creds():
    with open(CREDS_PATH) as f:
        return json.load(f)


def export_bib(creds) -> str:
    """Eksportuje wszystkie pozycje z grupy Zotero jako BibTeX."""
    print("📚 Łączę z Zotero...")
    zot = zotero.Zotero(creds["sylvarumGroupID"], "group", creds["apiKey"])

    print("⬇️  Pobieram pozycje...")
    items = zot.everything(zot.top())
    print(f"   Znaleziono {len(items)} pozycji.")

    bibtex_chunks = []
    for item in items:
        item_key = item["key"]
        try:
            bib = zot.item(item_key, format="bibtex")
            if bib and bib.strip():
                bibtex_chunks.append(bib.strip())
        except Exception as e:
            print(f"   ⚠️  Pominięto {item_key}: {e}")

    return "\n\n".join(bibtex_chunks) + "\n"


def validate(bib_path: Path) -> bool:
    """Uruchamia validate_bib.py. Zwraca True jeśli OK."""
    result = subprocess.run(
        [PYTHON, str(VALIDATE_SCRIPT), str(bib_path)],
        capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
        return False
    return True


def git_sync(bib_path: Path) -> bool:
    """Commituje i pushuje bibliography.bib."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(
            ["git", "add", str(bib_path)],
            cwd=WORKSPACE, check=True, capture_output=True
        )
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            print("✅ Brak zmian — bibliografia aktualna.")
            return True

        subprocess.run(
            ["git", "commit", "-m", f"chore: sync bibliography from Zotero ({now})"],
            cwd=WORKSPACE, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=WORKSPACE, check=True, capture_output=True
        )
        print(f"🚀 Wypchnięto do GitHub.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e.stderr.decode() if e.stderr else e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sync Zotero → GitHub")
    parser.add_argument("--dry-run", action="store_true", help="Eksport + walidacja bez commita")
    parser.add_argument("--export-only", action="store_true", help="Tylko eksport, bez walidacji i commita")
    args = parser.parse_args()

    creds = load_creds()

    # 1. Eksport
    bib_content = export_bib(creds)
    BIB_PATH.parent.mkdir(parents=True, exist_ok=True)
    BIB_PATH.write_text(bib_content, encoding="utf-8")
    print(f"💾 Zapisano: {BIB_PATH}")

    if args.export_only:
        return

    # 2. Walidacja
    print("🔍 Walidacja...")
    if not validate(BIB_PATH):
        print("❌ Walidacja nie przeszła — commit wstrzymany.")
        sys.exit(1)

    if args.dry_run:
        print("ℹ️  Dry-run — pomijam commit.")
        return

    # 3. Git sync
    git_sync(BIB_PATH)


if __name__ == "__main__":
    main()
