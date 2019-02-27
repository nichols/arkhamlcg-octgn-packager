#!/usr/bin/env python3

# TODO: add module description

import sys
import re
import requests
import arkham_data
from bs4 import BeautifulSoup

suffix_1000_per_page = '?per_page=1000'

# cardgamedb urls look like this:
# http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/the-path-to-carcosa-cycle/the-pallid-mask/

class SetScrapingError(Exception):
    """Base class for exceptions in this module."""
    pass




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
            m = re.match('([^:]+):\s*([^:<]*)\s*)', f.text)
            if m:
                field, value = m.groups()
                value = value.strip()
                if field == 'Number':
                    if re.match('^\d+[ab]$'):   # remove a/b from end of number if it's there
                        value = value[:-1]
                    card['number'] = value
                elif field == 'Quantity':
                    card['quantity'] = value
                elif field == 'Encounter Set':
                    card['encounter_set'] = value
                elif field == 'Clue Threshold':
                    card['front']['clues'] = value
                elif field == 'Illustrator':    # we don't need this field
                    continue
                else:   # assume this is a normal field that goes in side data
                    card['front']['data'][field] = value
            elif f.text.strip() == "skills":
                continue
            else:
                error_msg = 'While scraping url {}, found div tag with unexpected text {}'.format(url, f.text.strip())
                raise SetScrapingError(error_msg)

        elif 'traits' in f['class']:
            card['front']['data']['Traits'] = f.text
        elif 'flavorText' in f['class']:
            card['front']['data']['Flavor Text'] = f.text
        elif 'gameText' in f['class']:
            if 'Text' not in card['front']['data']:
                card['front']['data']['Text'] = f.text
            elif 'back' in card:    # this must be the back side text
                card['back']['data']['Text'] = f.text
            elif f.text.strip():
                error_msg = 'While scraping url {}, found nonempty second text tag, but only one image'.format(url)
                raise SetScrapingError(error_msg)
        elif 'skills' in f['class'] or 'stats' in f['class']:   # don't need these
            continue
        else:
            error_msg = 'While scraping url {}, found div tag with unexpected class {}'.format(url, f['class'])
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
        print("args: cardgamedb_url")
        return

    url = sys.argv[1]
    arkhamset = scrape_set_from_url(url)

    path = arkham_data.create_set_file(arkhamset)
    print("Wrote set data to {}".format(path))


if __name__ == '__main__':
    main()
