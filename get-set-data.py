#!/usr/bin/env python3

# Input:  url of a set on cardgamedb, e.g.
#         'http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/guardians-of-the-abyss/'
# 
# Output: 'created <set-name>.json'
#
# Creates a .json file containing all the cards in the set.


import requests 
import re
import json
import sys
import getopt
from bs4 import BeautifulSoup

card_fields = ['name', 'game_number', 'cycle_number', 'quantity', 'illustrator', 'type', 'encounter_set', 'encounter_set_number', 'traits', 'game_text', 'flavor_text', 'class', 'level', 'willpower', 'intellect', 'combat', 'agility', 'wild']

# only reason for this regex is to get the card's game_number
card_link_prefix = 'http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/'
card_link_pattern = '([a-zA-Z_\-]+)/([a-zA-Z_\-]+)/([^/])+-r(\d+)'
suffix_1000_per_page = '?per_page=1000'


def get_set(url):
    page = requests.get(url).text
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
    return {'setname': setname, 'cards': cards}


def get_card(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    fields = soup.find('div', 'cardText').find_all('div') 
    
    card = {'Name': soup.h1.string.strip()}
    sides = []
    for f in fields: 
        if not f.has_attr('class'):
            m = re.match('([^:]+):\s([^:]+)', f.text.strip())
            if m:
                fieldname, value = m.groups()
                if fieldname == 'Number':
                    card['set_number'] = value
                else:
                    card[fieldname] = value
        elif 'flavorText' in f['class']:
            card['flavor_text'] = f.text
        elif 'gameText' in f['class']:
            sides.append(f.text)
        elif 'traits' in f['class']:
            traits = [x.strip() for x in f.text.split('.')]
            card['traits'] = [trait for trait in traits if trait]
        
    while len(sides) < 2:
        sides.append(u'')
    card['text_front'] = sides[0]
    card['text_back'] = sides[1]
        
    imgs = soup.table.find_all('img')
    card['img_url_front'] = imgs[0]['src']
    if len(imgs) > 1:
        card['img_url_back'] = imgs[1]['src']
    else:
        card['img_url_back'] = u''

    # game_number must be read from the URL
    m = re.match(card_link_prefix + card_link_pattern, url)
    if m: 
        card['game_number'] = m.group(4)
    
    return card


def main():
    if len(sys.argv) < 2:
        print("get-set-data <cardgamedb_url>")
        return
    url = sys.argv[1]
    print("starting with url={}".format(url))
    my_set = get_set(url)
    output_filename = my_set['setname'] + '.json'
    with open(output_filename, 'w') as outfile:
        json.dump(my_set, outfile)
    print("created {}".format(output_filename))


if __name__ == '__main__':
    main()
