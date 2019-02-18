#!/usr/bin/env python3

# Input: JSON file containing metadata for a set of cards, including URLs of card images
# Creates necessary directories and files to load this set into OCTGN

"""
OCTGN package schema:

<OCTGN directory>
  Decks
    Arkham Horror - The Card Game
      <CycleNumber> - <CycleName>
        <ScenarioNumber> - <ScenarioName>.o8d   # or for standalones, <StandaloneScenarioName> - <Version>.o8d
  GameDatabase
    a6d114c7-2e2a-4896-ad8c-0330605c90bf
      Decks
        <CycleNumber> - <CycleName>
          <ScenarioNumber> - <ScenarioName>.o8d 
      Sets
        <SetGUID>
          set.xml                               # XML file with metadata for all cards in this set
  ImageDatabase
    a6d114c7-2e2a-4896-ad8c-0330605c90bf
      Sets
        <SetGUID>
          Cards
            <CardGUID>.jpg
            <CardGUID>.b.jpg    # reverse side
            <CardGUID>.png      # PNGs are OK too

Scenarios are numbered as they are in the campaign guide, e.g. '1a - Extracurricular Activity'

"""

import json
import uuid
import sys
import subprocess
import os
import re
import requests
import shutil
from urllib.parse import urlparse

game_id = 'a6d114c7-2e2a-4896-ad8c-0330605c90bf'

cycles = {
        '01': 'Core',
        '02': 'The Dunwich Legacy',
        '03': 'The Path to Carcosa',
        '04': 'The Forgotten Age',
        '05': 'The Circle Undone',
}

standalones = {
        '101': 'Curse of the Rougarou',
        '102': 'Carnevale of Horrors',
        '103': 'Labyrinths of Lunacy',
        '104': 'Guardians of the Abyss',
}

returns = {
        '201': 'Return to The Night of the Zealot',
        '202': 'Return to The Dunwich Legacy',
}


def load_set_from_json(json_filename):
    # TODO: load scenario string here if needed

    with open(json_filename, 'r') as json_file:
        arkhamset = json.load(json_file)
    return arkhamset


def get_extension_from_url(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if not re.match('^\.\w+$', ext):
        raise ValueError
    return ext


def download_img(url, dest):
    r = requests.get(url, stream=True, headers={'User-agent': 'Mozilla/5.0'})
    if r.status_code == 200:
        with open(dest, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)


# collect just scenario (non-player) cards and make a deck file of them, put in correct directory
def create_scenario_o8d(arkhamset, path):
    pass


# make set.xml file containing metadata on all cards, put in correct directory
def create_set_xml(arkhamset, path):
    pass


# download all card images, set filename = GUID, put in correct directory
def create_card_image_files(arkhamset, path):
    for card in arkhamset['cards']:
        url_front = card['img_url_front']
        dest_front = path + card['id'] + get_extension_from_url(url_front)
        download_img(url_front, dest_front)
        
        url_back = card['img_url_back']
        if url_back:
            dest_back = path + card['id'] + ".b" + get_extension_from_url(url_back)
            download_img(url_back, dest_back)


def build_octgn_package(arkhamset):
    arkhamset['id'] = str(uuid.uuid4())
    for card in arkhamset['cards']:
        card['id'] = str(uuid.uuid4())

    decks_path = "Decks/Arkham Horror - The Card Game/" + cycle_string
    #gamedb_decks_path = "GameDatabase/" + game_id + "/" + decks_path  # don't need this
    gamedb_sets_path = "GameDatabase/" + game_id + "/Sets/" + arkhamset['id']
    imgdb_path = "ImageDatabase/" + game_id + "/Sets/" + arkhamset['id'] + "/Cards"

    scenario_o8d_path = decks_path + "/" + scenario_string + ".o8d"
    set_xml_path = gamedb_sets_path + "/set.xml"

    try:
        os.makedirs(decks_path)
        os.makedirs(gamedb_sets_path)
        os.makedirs(imgdb_path)
    except FileExistsError:
        # directory already exists
        raise

    create_scenario_o8d(arkhamset, scenario_o8d_path)
    create_set_xml(arkhamset, set_xml_path)
    create_card_image_files(arkhamset, imgdb_path)

    # now zip everything?





def main():
    if len(sys.argv) < 2:
        print("create-octgn-package.py <json file>")
        return

    json_filename = sys.argv[1]
    arkhamset = load_set_from_json(json_filename)
    print("loaded {}".format(arkhamset['setname']))
    
    # test card image download
    card_url = arkhamset['cards'][0]['img_url_front']
    ext = get_extension_from_url(card_url)
    dest = 'card_img' + ext
    download_img(card_url, dest)


if __name__ == '__main__':
    main()
