# Input:  url of a set on cardgamedb, e.g.
#         'http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/guardians-of-the-abyss/'
# 
# Output: 'created <set-name>.json'
#
# Creates a .json file containing all the cards in the set.


import urllib2
import re
from bs4 import BeautifulSoup
from collections import namedtuple

card = namedtuple('card', ['game_number', 'name', 'page_url'])

card_link_prefix = 'http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/'
card_link_pattern = '([a-zA-Z_\-]+)/([a-zA-Z_\-]+)/([^/])+-r(\d+)'
suffix_1000_per_page = '?per_page=1000'


def get_setname_and_cards(url):
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    setname = soup.h1.string.strip()
    
    cards = []
    links = [cardText.find('a') for cardText in soup.find_all('div', 'cardText')]
    for l in links:
        card_url = l['href'].strip()
        m = re.match(prefix + link_pattern, card_url)
        if m: 
            cardnum = m.group(4)
        else:
            cardnum = ''
        cardtitle = l.string.strip()
        c = card(game_number=cardnum, name=cardtitle, page_url=card_url)
        cards.append(c)
    return setname, cards


def test():
    url = 'http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/the-path-to-carcosa-cycle/the-pallid-mask/'
    url_with_suffix = url + suffix_1000_per_page
    setname, cards = get_setname_and_cards(url_with_suffix)
    print "Set: {}".format(setname)
    for c in cards:
        print c


if __name__ == '__main__':
    test()

