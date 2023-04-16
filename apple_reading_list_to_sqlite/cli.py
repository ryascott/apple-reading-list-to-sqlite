import datetime
import json
import pathlib
import plistlib
from typing import Optional

import click
import httpx
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
        file_contents = extract_file_contents(SAFARI_BOOKMARKS_PLIST)
        for list_item in process_file_contents(file_contents, fetch_content):
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

        file_contents = extract_file_contents(SAFARI_BOOKMARKS_PLIST)
        reading_list = process_file_contents(file_contents, fetch_content)
        total = 0
        for value in track(reading_list, description="Inserting Into Database.."):
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


def extract_file_contents(file_path: pathlib.Path) -> dict:
    """
    Extract the contents of the plist file and return a dictionary
    :param file_path: The path of the file with the filename included to extract
    :return: A dictionary of the contents of the plist file
    """

    reading_list_file = pathlib.Path(f"{file_path}").expanduser().absolute()
    try:
        with open(reading_list_file, "rb") as plist_file:
            plist = plistlib.load(plist_file)
    except FileNotFoundError:
        raise click.UsageError(
            f"Could not find Reading File List at file at {file_path}"
        )
    return plist


def process_file_contents(file_contents: dict, fetch_content: bool) -> list[dict]:
    """
    Process the contents of the plist file and return a list of dictionaries

    :param file_contents: The contents of the plist file as a dictionary
    :param fetch_content: Retrieve the content of the URL of the list item
    :return:
    """

    bookmarks = [
        child["Children"]
        for child in file_contents["Children"]
        if "com.apple.ReadingList" in child["Title"]
    ][0]
    reading_list = []
    for bookmark in track(bookmarks, "Processing File Contents..."):
        url = bookmark["URLString"]
        text = bookmark["ReadingList"].get("PreviewText", "")
        date_added = bookmark["ReadingList"].get("DateAdded", None)
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
