#!/usr/bin/env python3
"""
Zotero Tool — Bibliotekarz z Niewidocznego Uniwersytetu
Zarządza grupą Sylvarum (ID: 6137135)

Użycie:
  python3 zotero_tool.py list [--collection <name>]
  python3 zotero_tool.py search <query>
  python3 zotero_tool.py add --url <url>
  python3 zotero_tool.py add --title <title> --author <author> --year <year> [--type <type>]
  python3 zotero_tool.py collections
  python3 zotero_tool.py info <item_key>
"""

import json
import sys
import argparse
from pathlib import Path
from pyzotero import zotero

# Load credentials
CREDS_PATH = Path(__file__).parent.parent / "memory" / "zotero.json"
with open(CREDS_PATH) as f:
    creds = json.load(f)

GROUP_ID = creds["sylvarumGroupID"]
API_KEY = creds["apiKey"]

# Connect to Sylvarum group
zot = zotero.Zotero(GROUP_ID, "group", API_KEY)


def list_items(collection_name=None, limit=20):
    if collection_name:
        cols = zot.collections()
        match = next((c for c in cols if c["data"]["name"].lower() == collection_name.lower()), None)
        if not match:
            print(f"Kolekcja '{collection_name}' nie znaleziona.")
            all_names = [c["data"]["name"] for c in cols]
            print(f"Dostępne kolekcje: {', '.join(all_names)}")
            return
        items = zot.collection_items(match["key"], limit=limit)
    else:
        items = zot.items(limit=limit)
    
    print(f"Znaleziono {len(items)} pozycji:\n")
    for i, item in enumerate(items, 1):
        data = item["data"]
        title = data.get("title", "(bez tytułu)")
        year = data.get("date", "")[:4] if data.get("date") else ""
        item_type = data.get("itemType", "")
        creators = data.get("creators", [])
        author = creators[0].get("lastName", "") if creators else ""
        print(f"{i:3}. [{item['key']}] {title}")
        if author or year:
            print(f"       {author}{', ' + year if year else ''} ({item_type})")


def search_items(query, limit=20):
    items = zot.items(q=query, limit=limit)
    print(f"Wyniki dla '{query}': {len(items)} pozycji\n")
    for i, item in enumerate(items, 1):
        data = item["data"]
        title = data.get("title", "(bez tytułu)")
        year = data.get("date", "")[:4] if data.get("date") else ""
        creators = data.get("creators", [])
        author = creators[0].get("lastName", "") if creators else ""
        url = data.get("url", "")
        print(f"{i:3}. [{item['key']}] {title}")
        if author or year:
            print(f"       {author}{', ' + year if year else ''}")
        if url:
            print(f"       URL: {url}")


def list_collections():
    cols = zot.collections()
    print(f"Kolekcje w Sylvarum ({len(cols)}):\n")
    for c in cols:
        name = c["data"]["name"]
        key = c["key"]
        count = c["meta"].get("numItems", "?")
        print(f"  [{key}] {name} ({count} pozycji)")


def item_info(key):
    item = zot.item(key)
    data = item["data"]
    print(json.dumps(data, indent=2, ensure_ascii=False))


def add_by_url(url):
    """Dodaj pozycję z URL (Zotero spróbuje pobrać metadane)."""
    result = zot.add_item_via_identifier(url)
    print(f"Dodano: {result}")


def add_manual(title, author=None, year=None, item_type="journalArticle", url=None, note=None):
    """Ręcznie dodaj pozycję."""
    template = zot.item_template(item_type)
    template["title"] = title
    if year:
        template["date"] = str(year)
    if url:
        template["url"] = url
    if author:
        parts = author.split(" ", 1)
        template["creators"] = [{
            "creatorType": "author",
            "firstName": parts[0] if len(parts) > 1 else "",
            "lastName": parts[-1]
        }]
    resp = zot.create_items([template])
    key = list(resp["successful"].keys())[0] if resp.get("successful") else None
    if key:
        item_key = resp["successful"][key]["key"]
        print(f"Dodano pozycję: [{item_key}] {title}")
        if note:
            note_template = zot.item_template("note")
            note_template["note"] = note
            note_template["parentItem"] = item_key
            zot.create_items([note_template])
            print(f"  + notatka dodana")
    else:
        print(f"Błąd: {resp}")


def main():
    parser = argparse.ArgumentParser(description="Zotero Sylvarum Tool")
    subparsers = parser.add_subparsers(dest="command")

    # list
    p_list = subparsers.add_parser("list", help="Lista pozycji")
    p_list.add_argument("--collection", "-c", help="Filtruj po kolekcji")
    p_list.add_argument("--limit", "-n", type=int, default=20)

    # search
    p_search = subparsers.add_parser("search", help="Szukaj pozycji")
    p_search.add_argument("query")
    p_search.add_argument("--limit", "-n", type=int, default=20)

    # collections
    subparsers.add_parser("collections", help="Lista kolekcji")

    # info
    p_info = subparsers.add_parser("info", help="Szczegóły pozycji")
    p_info.add_argument("key")

    # add
    p_add = subparsers.add_parser("add", help="Dodaj pozycję")
    p_add.add_argument("--url", help="URL do pobrania metadanych")
    p_add.add_argument("--title", help="Tytuł")
    p_add.add_argument("--author", help="Autor (Imię Nazwisko)")
    p_add.add_argument("--year", help="Rok")
    p_add.add_argument("--type", dest="item_type", default="journalArticle")
    p_add.add_argument("--note", help="Notatka")

    args = parser.parse_args()

    if args.command == "list":
        list_items(args.collection, args.limit)
    elif args.command == "search":
        search_items(args.query, args.limit)
    elif args.command == "collections":
        list_collections()
    elif args.command == "info":
        item_info(args.key)
    elif args.command == "add":
        if args.url and not args.title:
            add_by_url(args.url)
        elif args.title:
            add_manual(args.title, args.author, args.year, args.item_type, args.url, args.note)
        else:
            print("Podaj --url lub --title")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
