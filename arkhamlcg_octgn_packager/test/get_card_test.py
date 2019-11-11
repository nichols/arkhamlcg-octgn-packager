
import unittest
import os.path

from bs4 import BeautifulSoup
from unittest.mock import patch
from arkhamlcg_octgn_packager.cardgamedb_scraper import get_card_dict_from_soup
from arkhamlcg_octgn_packager.arkham_lib import Card

AZATHOTH_FILENAME = 'card_azathoth.html'
AZATHOTH_TITLE = 'Azathoth'
AZATHOTH_NUMBER = 346

DIAGRAMS_FILENAME = 'card_anatomical_diagrams.html'
DIAGRAMS_TITLE = 'Anatomical Diagrams'
DIAGRAMS_NUMBER = 108

PETE_FILENAME = 'card_ashcan_pete.html'
PETE_TITLE = '“Ashcan” Pete'
PETE_NUMBER = 5

def get_soup_from_file(filename):
    path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, 'r') as html_file:
        return BeautifulSoup(html_file.read(), 'html.parser')

class PlayerCardSoupTestCase(unittest.TestCase):

    def testAzathoth(self):
        soup = get_soup_from_file(AZATHOTH_FILENAME)
        card_dict = get_card_dict_from_soup(soup)
        card = Card.from_cardgamedb(card_dict)
        self.assertEqual(card.front.title, AZATHOTH_TITLE)
        self.assertEqual(card.set_number, AZATHOTH_NUMBER)
        self.assertTrue(card.front.unique)

    def testDiagrams(self):
        soup = get_soup_from_file(DIAGRAMS_FILENAME)
        card_dict = get_card_dict_from_soup(soup)
        card = Card.from_cardgamedb(card_dict)
        self.assertEqual(card.front.title, DIAGRAMS_TITLE)
        self.assertEqual(card.set_number, DIAGRAMS_NUMBER)

    def testPete(self):
        soup = get_soup_from_file(PETE_FILENAME)
        card_dict = get_card_dict_from_soup(soup)
        card = Card.from_cardgamedb(card_dict)
        self.assertEqual(card.front.title, PETE_TITLE)
        self.assertEqual(card.set_number, PETE_NUMBER)
        self.assertTrue(card.front.unique)

if __name__ == "__main__":
    unittest.main()
