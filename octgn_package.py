# TODO: add module description
# TODO: cardgamedb doesn't have mini cards, so figure out a way to get those

import uuid
import os
import re
import requests
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

game_id = 'a6d114c7-2e2a-4896-ad8c-0330605c90bf'

# octgn encoding of the five skill icons
skill_icon_symbols = {
    'Willpower': 'ά',
    'Intellect': 'έ',
    'Combat': 'ή',
    'Agility': 'ί',
    'Wild': 'ΰ',
}

# TODO: fill in missing symbols
 octgn_symbol_map = {
    '[Willpower]': 'ά',
    '[Intellect]': 'έ',
    '[Combat]': 'ή',
    '[Agility]': 'ί',
    '[Wild]': 'ΰ',
    '[Action]': 'η',
    '[Reaction]': '',
    '[Free]': '',
    '[Guardian]': '',
    '[Seeker]': '',
    '[Rogue]': '',
    '[Mystic]': '',
    '[Survivor]': '',
    '[Skull]': '',
    '[Cultist]': '',
    '[Tablet]': '',
    '[Elder Thing]': '',
    '[Auto-fail]': '',
    '[Elder Sign]': '',
    '[Investigators]': 'π',
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
        return True
    else:
        return False


def get_card_size(card):
    # possible values: 'InvestigatorCard', 'HorizCard', 'EncounterCard', 'MiniCard'
    if (card['front']['Subtype'] == 'Basic Weakness'
            or card['front']['Type'] in ('Asset', 'Skill', 'Event', 'Investigator')):
        return 'InvestigatorCard'
    elif card['front']['Type'] in ('Location', 'Treachery', 'Enemy'):
        return 'EncounterCard'
    elif card['front']['Type'] in ('Act', 'Agenda'):
        return 'HorizCard'
    else:
        return ''


# convert cardgamedb card text into OCTGN xml card text
def to_octgn_format(text):
    # TODO: handle any weird XML stuff?
    for k, v in octgn_symbol_map.items():
        text = text.replace(k, v)
    return text


def reformat_side_fields_for_octgn(side):
    for field in arkham_common.side_data_fields_with_possible_symbols:
        if field in side['data']:
            side['data'][field] = to_octgn_format(side['data'][field])


# convert skill icon info in cardgamedb format into OCTGN format (single string)
# delete original skill fields from side data dict
def make_skill_icons_string_for_side(side):
    icons_string = ''
    for skill, symbol in skill_icon_symbols.items():
        num_icons = int(side.get(skill, 0))
        icons_string += (symbol * num_icons)
    side['Skill Icons'] = icons_string
    del side['Willpower']
    del side['Intellect']
    del side['Combat']
    del side['Agility']
    del side['Wild']


def make_slot_strings_for_side(side):
    # TODO: handle double hand and arcane slots, handle weird stuff like flamethrower
    pass


def reformat_side_for_octgn(side):
    if side['data'].get('Type', '') in ['Asset', 'Skill', 'Event']:
        make_skill_icons_string_for_side(side)
    if side['data'].get('Type', '') == 'Asset':
        make_slot_strings_for_side(side)
    reformat_side_fields_for_octgn(side)


def reformat_card_for_octgn(card):
    reformat_side_for_octgn(card['front'])
    if arkham_common.is_double_sided(card):
        reformat_side_for_octgn(card['back'])


def card_to_xml(card):
    if 'id' not in card:
        card['id'] = uuid.uuid4()
    size = get_card_size(card)
    front_attrib = {'id': card['id'], 'name': card['front']['name'], 'size': size}
    front_root = ET.Element('card', front_attrib)

    make_skill_icons_strings_for_card(card)
    make_slot_strings_for_card(card)
    reformat_card_fields_for_octgn(card)

    ET.subElement(front_root, 'property', {'name': 'Card Number', 'value': card['number']})
    ET.subElement(front_root, 'property', {'name': 'Quantity', 'value': card['Quantity']})
    ET.subElement(front_root, 'property', {'name': 'Encounter Set', 'value': card['Encounter Set']})
    for k, v in card['front']['data'].items():
        ET.SubElement(front_root, 'property', {'name': k, 'value': v})

    if arkham_common.is_double_sided(card):
        back_attrib = {'name': card['back']['name'], 'size': size, 'type': 'B'}
        back_root = ET.SubElement(front_root, 'alternate', back_attrib)
        ET.subElement(back_root, 'property', {'name': 'Encounter Set', 'value': card['Encounter Set']})
        for k, v in card['back']['data'].items():
            ET.SubElement(back_root, 'property', {'name': k, 'value': v})

    return front_root


# make set.xml file containing metadata on all cards
def create_set_xml(arkhamset, path):
    path += '/set.xml'
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

    # TODO: figure out XML header? Or generate it with options of ET.write()?
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

    # TODO: handle exceptions or whatever
    # TODO: make the xml file pretty (new line for each tag, indented, etc)
    xml_tree = ET.ElementTree(set_root)
    xml_tree.write(path, encoding='UTF-8', xml_declaration=True)
    return path


# download all card images, set filename = GUID, put in correct directory
def create_card_image_files(arkhamset, path):
    num = 0
    for card in arkhamset['cards']:
        url_front = card['front']['image_url']
        dest_front = path + '/' + card['id'] + get_extension_from_url(url_front)
        if download_img(url_front, dest_front):
            num += 1

        if arkham_common.is_double_sided(card):
            url_back = card['back']['image_url']
            dest_back = path + '/' + card['id'] + '.b' + get_extension_from_url(url_back)
            if download_img(url_back, dest_back):
                num += 1

    return num
    # TODO: handle exceptions or whatever


def create_scenario_o8d_file(scenario, path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

    path += "/{} - {}.o8d".format(scenario['scenario_code'], scenario['name'])

    deck_attrib = {'game': game_id, sleeveid: '0'}
    deck_root = ET.Element('deck', deck_attrib)
    for section in ['Investigator', 'Special', 'Asset', 'Event', 'Skill',
                    'Weakness', 'Sideboard', 'Basic Weaknesses']:
        ET.SubElement(deck_root, 'section', {'name': section, 'shared': 'False'})

    for section in ['Agenda', 'Act', 'Encounter', 'Location', 'Setup']:
        section_root = ET.SubElement(deck_root, 'section', {'name': section, 'shared': 'True'})
        for card in scenario.get(section, []):
            card_attrib = {'qty': card['quantity'], 'id': card['id'], }
            card_tag = ET.SubElement(section_root, 'card', {})
            card_tag.text = card['front']['name']

    for section in ['Special', 'Second Special', 'Chaos Bag']:
        ET.SubElement(deck_root, 'section', {'name': section, 'shared': 'True'})

    notes = ET.SubElement(deck_root, 'notes')
    notes.text = "<![CDATA[]]>"

    xml_tree = ET.ElementTree(deck_root)
    xml_tree.write(path, encoding='UTF-8', xml_declaration=True)
    return path


def create_octgn_package(arkhamset):
    if 'id' not in arkhamset or not arkhamset['id']:
        arkhamset['id'] = uuid.uuid4()

    # TODO: raise exception if campaign string isn't well-formed
    campaign_string = arkhamset['campaign_code'] + ' - ' + arkhamset['campaign']
    decks_path = "Decks/Arkham Horror - The Card Game/" + campaign_string
    gamedb_decks_path = "GameDatabase/" + game_id + "/Decks/" + campaign_string

    gamedb_sets_path = "GameDatabase/" + game_id + "/Sets/" + arkhamset['id']

    imagedb_path = "ImageDatabase/" + game_id + "/Sets/" + arkhamset['id'] + "/Cards"

    path = create_set_xml(arkhamset, gamedb_sets_path)
    print("created set XML file {}.".format(path))
    num = create_card_image_files(arkhamset, imagedb_path)
    print("created {} card image files in {}.".format(num, imagedb_path))

    for scenario in arkhamset['scenarios']:
        path = create_scenario_o8d_file(scenario, decks_path)
        print("created scenario file {}.".format(path))
        try:
            os.makedirs(decks_path)
        except FileExistsError:
            pass
        _, filename = os.path.split(path)
        new_path = decks_path + "/" + filename
        shutil.copy(path, new_path)
        print("copied to {}.".format(new_path))

    # TODO: zip directory tree at the end?
    # TODO: return path to created directory or archive
    path = ''
    return path
