import pathlib

import pytest
from typer.testing import CliRunner

from apple_reading_list_to_sqlite.cli import app

runner = CliRunner()


def test_dump():
    result = runner.invoke(app, ["--dump"])
    assert result.exit_code == 0
    assert result.output.startswith("{")
    assert result.output.strip().endswith("}")


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
