import click
import pytest
from sqlite_utils import Database
from typer.testing import CliRunner

from apple_reading_list_to_sqlite.cli import app

runner = CliRunner()


def test_dump():
    result = runner.invoke(app, ["--dump"])
    assert result.exit_code == 0


def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    result = runner.invoke(app, [str(db_path)])
    assert result.exit_code == 0
    assert db_path.exists()
    assert db_path.stat().st_size > 0


def test_usage_error_raised():
    result = runner.invoke(app, [])
    assert 2 == result.exit_code
    assert (
        "Please specify a path to a database file, or use --dump to see the output"
    ) in result.output.strip()


def test_fts_search_enabled(tmp_path):
    db_path = tmp_path / "testfts.db"
    result = runner.invoke(app, [str(db_path), "--enable-fts"])
    assert result.exit_code == 0
    assert db_path.exists()
    assert db_path.stat().st_size > 0
    db = Database(db_path)
    assert db["reading_list"].detect_fts() == "reading_list_fts"


@pytest.mark.macos
def test_extract_file_contents():
    from apple_reading_list_to_sqlite.cli import extract_file_contents

    file_contents = extract_file_contents("~/Library/Safari/Bookmarks.plist")

    assert isinstance(
        file_contents, dict
    ), "Expected return value to be a dictionary, but got {}".format(
        type(file_contents)
    )


def test_extract_file_contents_with_bad_filename():
    from apple_reading_list_to_sqlite.cli import extract_file_contents

    with pytest.raises(click.UsageError):
        extract_file_contents("~/Library/Safari/Bookmark.plist")


def test_process_file_contents():
    from apple_reading_list_to_sqlite.cli import process_file_contents

    file_contents = {
        "Children": [
            {
                "Title": "com.apple.ReadingList",
                "Children": [
                    {
                        "Title": "sqlite-utils",
                        "URLString": "https://sqlite-utils.datasette.io/en/stable/",
                        "WebBookmarkUUID": "E9F9B9B9-1B9C-4B0C-9B9B-9B9B9B9B9B9B",
                        "ReadingList": {
                            "PreviewText": "sqlite-utils 3.30",
                            "DateAdded": "2021-01-13T16:00:00Z",
                        },
                        "URIDictionary": {
                            "title": "sqlite-utils",
                            "bookmark": "https://sqlite-utils.datasette.io/en/stable/",
                        },
                    }
                ],
            }
        ]
    }

    results = process_file_contents(file_contents, False)
    assert results == [
        {
            "content": None,
            "date_added": "2021-01-13T16:00:00Z",
            "text": "sqlite-utils 3.30",
            "title": "sqlite-utils",
            "url": "https://sqlite-utils.datasette.io/en/stable/",
        }
    ]
