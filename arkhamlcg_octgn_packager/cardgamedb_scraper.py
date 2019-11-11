#!/usr/bin/env python3

# module for creating an Arkham Horror LCG set object (as described in
# arkham_common) by scraping data from cardgamedb.com

# cardgamedb urls look like this:
# http://www.cardgamedb.com/index.php/arkhamhorror/arkham-horror-the-card-game/_/the-path-to-carcosa-cycle/the-pallid-mask/

import logging
import sys
import re
import requests
from bs4 import BeautifulSoup

class SetScrapingError(Exception):
    """Base class for exceptions in this module."""
    pass

_suffix_1000_per_page = '?per_page=1000'

_unique_symbol_card_title_regex = re.compile(r"^(&bull;|•|\uf261)\s*(.+)")
_investigators_symbol_regex = re.compile(r"\udb88\udd83|\uf2183|\[per_investigator\]")

def _parse_card_title_for_uniqueness(title):
    m = _unique_symbol_card_title_regex.match(title)
    if m:
        return m.group(2), True
    return title, False

# Translate some symbols that are represented strangely on the cardgamedb set
# page into human-readable symbols.
def _replace_cardgamedb_symbols(text):
    return _investigators_symbol_regex.sub("[Investigators]", text)

# Process a list of tags containing strings of the form "Key: Value", return
# a dict containing these items.
def _tags_to_dict(tags):
    elements = dict()
    for tag in tags:
        try:
            k, v = tag.text.strip().split(": ", 1)
            elements[k] = _replace_cardgamedb_symbols(v)
        except ValueError:
            continue
    return elements

def _get_soup_from_url(url):
    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
    if not response:
        raise SetScrapingError(
            "Couldn't get {} (status code {})".format(url, response.status_code))
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# Process a cardgamedb card page and return a dict of card fields. Some of these
# fields (like 'title') usually only apply to the front of a double-sided card,
# while others (like 'Number') are the same for both sides. But cardgamedb
# usually doesn't have any info on the back of a card except for the text.

def get_card_dict_from_soup(soup):
    imgs_td = soup.find("table", class_="ipb_table").find("tr").find("td")
    card_td = imgs_td.find_next_sibling()
    card_text = card_td.h1.find_next_sibling()

    try:
        gameTexts = [_replace_cardgamedb_symbols(x.text.strip())
                         for x in card_text.find_all("div", class_="gameText")]
        imgs = [i["src"] for i in imgs_td.find_all("img")]
        traits_string = card_text.find("div", class_="traits").text.strip()
        traits = traits_string.split(". ") if traits_string else []
        cardTitle, unique = _parse_card_title_for_uniqueness(
            card_td.h1.find("div", class_="cardTitle").text.strip())
        cardSubTitle = (
            card_td.h1.find("div", class_="cardSubTitle").text.strip()
            or None)
        flavorText = card_text.find("div", class_="flavorText").text.strip() or None
        other_kwargs = _tags_to_dict(card_text.find_all("div", class_=False))
    except:
        print("Exception while looking at card ")

    card_dict = dict(
        imgs=imgs,
        cardTitle=cardTitle,
        cardSubTitle=cardSubTitle,
        traits=traits,
        flavorText=flavorText,
        gameTexts=gameTexts,
        unique=unique,
        **other_kwargs)
    return card_dict

def get_card_dict_from_url(url):
    soup = _get_soup_from_url(url)
    return _get_card_dict_from_soup(soup)

def _guess_set_type(cards):
    total_cards = sum((int(c.get('Quantity', 1)) for c in cards))
    if total_cards < 5:
        return 'Promo'

    has_encounter_cards = any((
            lambda c : 'Class' not in c or c['Class'] == 'Mythos'
            for c in cards))
    has_player_cards = any((
            lambda c : 'Class' in c and c['Class'] != 'Mythos'
            for c in cards))
    has_investigator_cards = has_player_cards and any((
            lambda c : c.get('Type') == 'Investigator'
            for c in cards))

    if has_investigator_cards:
        return "Expansion"
    elif has_player_cards and total_cards == 60:
        return "Mythos Pack"
    elif has_player_cards:
        return "Other"
    else:
        return "Scenario Pack"

def get_set_dict_from_soup(soup, set_type=None):
    set_name = soup.h1.string.strip()

    # TODO: target a specific part of the tree to make this faster
    links = (cardText.find('a')['href'].strip()
            for cardText in soup.find_all('div', class_='cardText'))
    cards = [get_card_dict_from_soup(_get_soup_from_url(l)) for l in links]
    if set_type is None:
        set_type = _guess_set_type(cards)
        print("Guessed set_type = {}.".format(set_type))

    return dict(
        name=set_name,
        type=set_type,
        cards=cards,
    )

def get_set_dict_from_url(url):
    soup = _get_soup_from_url(url)
    return _get_set_dict_from_soup(soup)
