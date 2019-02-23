#!/usr/bin/env python3

# Input: path of json file containing metadata for a set of cards
# Such a json file can be produced by get-set-data.py

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

"""
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
##TODO: somehow use this to generate scenario_string for a given set if applicable
"""

import uuid
import sys
import os
import re
import requests
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'

def get_sheets_api_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service

game_id = 'a6d114c7-2e2a-4896-ad8c-0330605c90bf'

# octgn encoding of the five skill icons
skill_icon_symbols = {
    'Willpower': 'ά',
    'Intellect': 'έ',
    'Combat': 'ή',
    'Agility': 'ί',
    'Wild': 'ΰ',
}


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


def is_double_sided(card):
    return ('_image_url_back' in card) or ('_text_back' in card)


def get_card_size(card):
    ## TODO: guess card size based on type and fields.
    # possible values: 'InvestigatorCard', 'HorizCard', 'EncounterCard', 'MiniCard'
    return 'InvestigatorCard'


# convert cardgamedb card text into OCTGN xml card text
def reformat_card_text_for_octgn(text):
    ## TODO: handle special symbols and markup for xml
    return text


# convert skill icon info in cardgamedb format into OCTGN format (single string)
# delete original skill fields from card dict
def make_skill_icons_string(card):
    icons_string = ''
    for skill, symbol in skill_icon_symbols.items():
        num_icons = int(card[skill])
        icons_string += (symbol * num_icons)
    card['Skill Icons'] = icons_string
    del card['Willpower']
    del card['Intellect']
    del card['Combat']
    del card['Agility']
    del card['Wild']


def make_slots_string(card):
    ## TODO: handle number of hand slots, handle weird stuff like flamethrower
    pass


def card_to_xml(card):
    size = get_card_size(card)
    front_attrib = {'id': card['_id'], 'name': card['Name'], 'size': size}
    front_root = ET.Element('card', front_attrib)

    # if this is a player card but not an investigator or mini card
    if card['Type'] in ['Asset', 'Skill', 'Event']:
        make_skill_icons_string(card)
    if 'Slots' in card:
        make_slots_string(card)
    card['Text'] = reformat_card_text_for_octgn(card['Text'])

    for k, v in card.items():
        if not k.startswith('_'):
            ET.SubElement(front_root, 'property', {'name': k, 'value': v})

    if is_double_sided(card):
        # note that the back might have a different name, but we don't know
        back_attrib = {'name': card['Name'], 'size': size, 'type': 'B'}
        back_root = ET.SubElement(front_root, 'alternate', back_attrib)
        back_text = reformat_card_text_for_octgn(card['_text_back'])
        ET.SubElement(back_root, 'property', {'name': 'Text', 'value': back_text})
        # the back might have more fields, but cardgamedb only gives us the text
        ## TODO: update other back properties if possible

    return front_root


# make set.xml file containing metadata on all cards
def create_set_xml(arkhamset, path):
    ## TODO: figure out XML header? Or generate it with options of ET.write()?
    set_attrib = {
        'xmlns:noNamespaceSchemaLocation': 'CardSet.xsd',   # is this right?
        'name': arkhamset['name'],
        'id': arkhamset['id'],
        'gameId': game_id,
        'gameVersion': '1.0.0.0',
        'version': '1.0.0',
    }
    set_root = ET.Element('set', set_attrib)
    cards = ET.SubElement(set_root, 'cards')
    for card in arkhamset['cards']:
        cards.append(card_to_xml(card))

    ## TODO: handle exceptions or whatever
    ## TODO: make the xml file pretty (new line for each tag, indented, etc)
    xml_tree = ET.ElementTree(set_root)
    xml_tree.write(path, encoding='UTF-8', xml_declaration=True)


# download all card images, set filename = GUID, put in correct directory
def create_card_image_files(arkhamset, path):
    for card in arkhamset['cards']:
        url_front = card['_image_url_front']
        dest_front = path + '/' + card['_id'] + get_extension_from_url(url_front)
        download_img(url_front, dest_front)

        if is_double_sided(card):
            url_back = card['_image_url_back']
            dest_back = path + '/' + card['_id'] + '.b' + get_extension_from_url(url_back)
            download_img(url_back, dest_back)
    ##TODO: handle exceptions or whatever


def build_octgn_package(arkhamset):
    # generate unique IDs for set and cards
    arkhamset['id'] = str(uuid.uuid4())
    for card in arkhamset['cards']:
        card['_id'] = str(uuid.uuid4())

    """
    # we're not generating .o8d file for now
    decks_path = "Decks/Arkham Horror - The Card Game/" + cycle_string
    gamedb_decks_path = "GameDatabase/" + game_id + "/" + decks_path
    scenario_o8d_path = decks_path + "/" + scenario_string + ".o8d"
    """

    gamedb_sets_path = "GameDatabase/" + game_id + "/Sets/" + arkhamset['id']
    imagedb_path = "ImageDatabase/" + game_id + "/Sets/" + arkhamset['id'] + "/Cards"
    set_xml_path = gamedb_sets_path + "/set.xml"

    ## TODO: it's probably better to create the needed directories inside the
    ## functions create_set_xml and create_card_image_files rather than do it here
    try:
        os.makedirs(gamedb_sets_path)
        os.makedirs(imagedb_path)
    except FileExistsError:
        # directory already exists
        raise

    print("made directories:")
    print("\t{}\n\t{}".format(gamedb_sets_path, imagedb_path))

    # create_scenario_o8d(arkhamset, scenario_o8d_path)

    create_set_xml(arkhamset, set_xml_path)
    print("created set XML file.")
    create_card_image_files(arkhamset, imagedb_path)
    print("created card image files.")

    ##TODO: handle exceptions or whatever
    ##TODO: zip directory tree at the end?


def main():
    if len(sys.argv) < 2:
        print("create-octgn-package.py <json file>")
        return

    json_filename = sys.argv[1]
    assert json_filename.endswith('.json')

    arkhamset = load_set_from_json(json_filename)
    build_octgn_package(arkhamset)


if __name__ == '__main__':
    main()