#!/usr/bin/env python3

# TODO: add module description

import sys
from arkham_json import load_set
from cardgamedb_scraper import scrape_set_from_url
from arkham_sheets import create_spreadsheet_for_set


"""
# from cardgamedb url
def main():
    if len(sys.argv) < 2:
        print("args: cardgamedb_url")
        return

    url = sys.argv[1]
    arkhamset = scrape_set_from_url(url)

    spreadsheet_url = create_spreadsheet_for_set(arkhamset)
    print('Spreadsheet URL: {0}'.format(spreadsheet_url))
"""


# from json
def main():
    if len(sys.argv) < 2:
        print("args: path of json file containing set data")
        return

    path = sys.argv[1]
    arkhamset = load_set(path)

    spreadsheet_url = create_spreadsheet_for_set(arkhamset)
    print('Spreadsheet URL: {0}'.format(spreadsheet_url))


if __name__ == '__main__':
    main()
