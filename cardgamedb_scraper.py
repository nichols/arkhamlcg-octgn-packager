# TODO: add module description

"""
# these are the fields we can get from cardgamedb and use in OCTGN unchanged
common_fields = ['Type', 'Class', 'Health', 'Sanity', 'Illustrator',
'Willpower', 'Intellect', 'Combat', 'Agility']

# these fields need to be constructed individually
special_fields = ['Card Number', 'Name', 'Traits', 'Text', 'Flavor Text']

# internal fields that will be read from cardgamedb but not directly used by OCTGN
internal_fields = ['_text_back', '_image_url_front', '_image_url_back']

# fields supported by OCTGN but not provided by cardgamedb
missing_fields = ['Subtype', 'Encounter Set', 'Unique', 'Shroud', 'Clues',
'Doom', 'Victory Points']
# the only one of these we really miss badly is Encounter Set
# these can be filled in manually in a spreadsheet

# Another cardgamedb limitation: we can't get any fields for the back side of
# the card except the text.
"""

import requests
import re
from bs4 import BeautifulSoup

suffix_1000_per_page = '?per_page=1000'


def get_card(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    fields = soup.find('div', 'cardText').find_all('div')

    card = {'Name': soup.h1.string.strip()}
    texts = []
    for f in fields:
        if not f.has_attr('class'):
            m = re.match('([^:]+):\s([^:]+)', f.text.strip())
            if m:
                field, value = m.groups()
                if field == 'Number':
                    field = 'Card Number'
                card[field] = value
        elif 'flavorText' in f['class']:
            card['Flavor Text'] = f.text
        elif 'gameText' in f['class']:
            texts.append(f.text)
        elif 'traits' in f['class']:
            card['Traits'] = f.text

    imgs = soup.table.find_all('img')
    card['_image_url_front'] = imgs[0]['src']
    card['Text'] = texts[0] if texts else u''

    if len(imgs) > 1:
        card['_image_url_back'] = imgs[1]['src']
        card['_text_back'] = texts[1] if len(texts) > 1 else u''

    return card


def scrape_set_from_url(url):
    page = requests.get(url + suffix_1000_per_page).text
    soup = BeautifulSoup(page, 'html.parser')
    setname = soup.h1.string.strip()

    cards = []
    links = [cardText.find('a') for cardText in soup.find_all('div', 'cardText')]
    for l in links:
        card_url = l['href'].strip()
        print("loading {}...".format(card_url))
        c = get_card(card_url)
        cards.append(c)
        print("\t...done.")
    return {'name': setname, 'cards': cards}
