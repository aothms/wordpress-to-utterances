# wordpress-to-utterances
Convert a wordpress XML export with comments to utterances github issues and comments

## Usage

Provide the following environment variables (use `set` on windows or `export` otherwise) and run the python script pointing to you wordpress XML export.

    set TOKEN=
    set REPO=
    set SITE_NAME=
    set URL=

    python wordpress-to-utterances.py <my_wordpress_export.xml>
