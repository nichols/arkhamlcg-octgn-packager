#!/usr/bin/env python3

# TODO: add module description

import sys
from arkham_common import create_set_file
from arkham_sheets import create_spreadsheet_for_set
from cardgamedb_scraper import scrape_set_from_url


# from cardgamedb url
def main():
    if len(sys.argv) < 2:
        print("args: cardgamedb_url")
        return

    url = sys.argv[1]
    arkhamset = scrape_set_from_url(url)
    json_path = create_set_file(arkhamset)
    print("Wrote set data to {}".format(json_path))

    spreadsheet_url = create_spreadsheet_for_set(arkhamset)
    print("Created spreadsheet at {}".format(spreadsheet_url))

if __name__ == '__main__':
    main()
