
import unittest
import os.path

from bs4 import BeautifulSoup
from unittest.mock import patch
from arkhamlcg_octgn_packager.cardgamedb_scraper import get_set_dict_from_soup
from arkhamlcg_octgn_packager.arkham_lib import CardSet

ECHOES_FILENAME = 'set_echoes_of_the_past.html'
ECHOES_NAME = 'Echoes of the Past'
ECHOES_CARDS = 41

DUMMY_CARD_FILENAME = 'card_anatomical_diagrams.html'

def get_soup_from_file(filename):
    path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, 'r') as html_file:
        return BeautifulSoup(html_file.read(), 'html.parser')

class PlayerCardSoupTestCase(unittest.TestCase):

    def testSomething(self):
        set_soup = get_soup_from_file(ECHOES_FILENAME)
        dummy_card_soup = get_soup_from_file(DUMMY_CARD_FILENAME)
        with patch(
                'arkhamlcg_octgn_packager.cardgamedb_scraper._get_soup_from_url',
                return_value=dummy_card_soup) as _get_soup_function:
            set_dict = get_set_dict_from_soup(set_soup)
        card_set = CardSet.from_cardgamedb(set_dict)
        self.assertEqual(card_set.name, ECHOES_NAME)
        self.assertEqual(len(card_set.cards), ECHOES_CARDS)

if __name__ == "__main__":
    unittest.main()
