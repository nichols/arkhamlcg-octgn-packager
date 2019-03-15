#!/usr/bin/env python3

# TODO: add module description

import sys
import re
import requests
import arkham_common
from bs4 import BeautifulSoup

suffix_1000_per_page = '?per_page=1000'

# cardgamedb urls look like this:
# http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/the-path-to-carcosa-cycle/the-pallid-mask/

class SetScrapingError(Exception):
    """Base class for exceptions in this module."""
    pass


cardgamedb_symbol_map = {
    '\udb88\udd83': '[Investigators]',
}


# replace weird encoding from cardgamedb with human-readable symbols
def to_sheets_format(text):
    for k, v in cardgamedb_symbol_map.items():
        text.replace(k, v)
    return text



def get_card_raw_data(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')

    name = soup.h1.string.strip()
    fields = soup.find('div', 'cardText').find_all('div')
    imgs = soup.table.find_all('img')

    return name, fields, imgs


def get_card(url):
    name, fields, imgs = get_card_raw_data(url)

    card = {
        'front': {  'name': name,
                    'image_url': imgs[0]['src'],
                    'data': {},
        }
    }

    if len(imgs) > 1:
        card['back'] = {
            'name': card['front']['name'],  # assume same name as front side
            'image_url': imgs[1]['src'],
            'data': {},
        }

    for f in fields:
        if not f.has_attr('class'):
            m = re.match('([^:]+):\s*([^:<]*)', f.text.strip())
            if m:
                field, value = m.groups()
                value = value.strip()
                if field == 'Number':
                    value, _ = arkham_common.get_number_and_face(value)
                    card['number'] = value
                elif field == 'Quantity':
                    card['quantity'] = value
                elif field == 'Encounter Set':
                    card['encounter_set'] = value
                elif field == 'Clue Threshold':
                    card['front']['clues'] = to_sheets_format(value)
                elif field == 'Illustrator':    # we don't need this field
                    continue
                else:   # assume this is a normal field that goes in side data
                    card['front']['data'][field] = to_sheets_format(value)
            elif f.text.strip() == "skills":
                continue
            else:
                error_msg = 'While scraping url {}, found div tag with unexpected text {}'.format(url, f.text.strip())
                raise SetScrapingError(error_msg)

        elif 'traits' in f['class']:
            card['front']['data']['Traits'] = f.text
        elif 'gameText' in f['class']:
            if 'Text' not in card['front']['data']:
                card['front']['data']['Text'] = to_sheets_format(f.text)
            elif 'back' in card:    # this must be the back side text
                card['back']['data']['Text'] = to_sheets_format(f.text)
            elif f.text.strip():
                error_msg = 'While scraping url {}, found nonempty second text tag, but only one image'.format(url)
                raise SetScrapingError(error_msg)
        elif 'skills' in f['class'] or 'stats' in f['class'] or 'flavorText' in f['class']:   # don't need these
            continue
        else:
            error_msg = 'While scraping url {}, found div tag with unexpected class {}'.format(url, f['class'])
            raise SetScrapingError(error_msg)

    card_number_check = card.get('number', '')
    if not re.match('^\d+$', card_number_check):
        error_msg = 'Bad or missing card number {} at url {}'.format(card_number_check, url)
        raise SetScrapingError(error_msg)

    return card


def scrape_set_from_url(url):
    page = requests.get(url + suffix_1000_per_page).text
    soup = BeautifulSoup(page, 'html.parser')
    setname = soup.h1.string.strip()
    print("scraping set\'{}\' from {}".format(setname, url))

    cards = []
    links = [cardText.find('a') for cardText in soup.find_all('div', 'cardText')]
    for l in links:
        card_url = l['href'].strip()
        print("loading {}...".format(card_url))
        c = get_card(card_url)
        cards.append(c)
        print("\t...done.")

    # TODO: try to guess the type based on available info

    return {'name': setname, 'cards': cards}


def main():
    if len(sys.argv) < 2:
        raise ValueError("Command line argument needed: cardgamedb URL of set")

    url = sys.argv[1]
    arkhamset = scrape_set_from_url(url)

    path = arkham_data.create_set_file(arkhamset)
    print("Wrote set data to {}".format(path))


if __name__ == '__main__':
    main()
