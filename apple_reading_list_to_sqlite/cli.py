import datetime
import json
import pathlib
import plistlib
from typing import Optional

import click
import httpx
import rich.pretty
import typer
from rich.progress import track
from sqlite_utils import Database

SAFARI_BOOKMARKS_PLIST = "~/Library/Safari/Bookmarks.plist"

app = typer.Typer()


@app.command()
def cli(
    db_path: Optional[pathlib.Path] = typer.Argument(
        None, file_okay=True, dir_okay=False
    ),
    fetch_content: bool = False,
    dump: bool = False,
    enable_fts: bool = False,
):
    if not db_path and not dump:
        raise click.UsageError(
            "Please specify a path to a database file, or use --dump to see the output",
        )

    if dump:
        for list_item in extract_list(SAFARI_BOOKMARKS_PLIST, fetch_content):
            typer.echo(json.dumps(list_item, indent=4, sort_keys=True, default=str))

    else:
        db = Database(db_path)
        if not db["reading_list"].exists():
            db["reading_list"].create(
                {
                    "id": str,
                    "title": str,
                    "url": str,
                    "text": str,
                    "date_added": datetime.datetime,
                    "content": str,
                },
                pk="id",
            )

        reading_list = extract_list(SAFARI_BOOKMARKS_PLIST, fetch_content)
        total = 0
        for value in track(reading_list, description="Processing..."):
            db["reading_list"].upsert(
                value, hash_id_columns=["url", "title", "date_added"]
            )
            total += 1
        if enable_fts:
            if not db["reading_list"].detect_fts():
                db["reading_list"].enable_fts(["title", "text", "content"])
            else:
                db["reading_list"].rebuild_fts()

        typer.echo(f"Processed {total} items")


def extract_list(file_path: str, fetch_content: bool = False):
    readling_list_file = pathlib.Path(f"{file_path}").expanduser().absolute()
    try:
        with open(readling_list_file, "rb") as plist_file:
            plist = plistlib.load(plist_file)
    except FileNotFoundError:
        raise click.UsageError(
            f"Could not find Reading File List at file at {file_path}"
        )

    return process_reading_list(fetch_content, plist)


def process_reading_list(fetch_content: bool, plist):
    bookmarks = [
        child["Children"]
        for child in plist["Children"]
        if "com.apple.ReadingList" in child["Title"]
    ][0]
    reading_list = []
    for bookmark in bookmarks:
        url = bookmark["URLString"]
        text = bookmark["ReadingList"].get("PreviewText", "")
        date_added = bookmark["ReadingList"].get("DateAdded", "")
        title = bookmark["URIDictionary"]["title"]
        content = None
        if fetch_content:
            try:
                content = httpx.get(url).text
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
        reading_list.extend(
            [
                {
                    "url": url,
                    "title": title,
                    "text": text,
                    "date_added": date_added,
                    "content": content,
                }
            ]
        )
    return reading_list
