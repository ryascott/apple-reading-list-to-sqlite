# apple-reading-list-to-sqlite

Export Apple Reading List to SQLite

## Install



## Usage

            $ apple-reading-list-to-sqlite --help
            Usage: apple-reading-list-to-sqlite [OPTIONS] [DB_PATH]

            Export Apple Reading List to SQLite

            Arguments:
            [DB_PATH]  Path to the SQLite database file.

            Options:
            --version  Show the version and exit.
            --help     Show this message and exit.
            --fetch-content / --no-fetch-content try and retrive the content of the article
            --dump / --no-dump Dump the reading list to stdout
            --enable-fts / --no-enable-fts Enable full text search

## Testing

Right now, all tests only run on macOS. You can run them with:

    $ pytest

To skip the tests that require macOS, use:

    $ pytest -m "not macos"

## Contributing

Contributions are welcome! Fork the repo, make a branch, and submit a PR.

## Thanks


   [Apple News to sqlite] (https://github.com/RhetTbull/apple-news-to-sqlite)

   [sqlite-utils] (https://github.com/simonw/sqlite-utils)

   [Reading List Extract] (https://gist.github.com/keith/4b4a2e1b0b9b1b0d0e0a)

## License

MIT License
