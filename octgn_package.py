# TODO: add module description
# TODO: add minicard automatically whenever we add an investigator card

import uuid
import os
import re
import requests
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import arkham_common

game_id = 'a6d114c7-2e2a-4896-ad8c-0330605c90bf'

campaign_ids = {
    'core set':             '0000f984-d06f-44cb-bf1c-d66a620acad8',
    'the dunwich legacy':   'dfa9b3bf-58f2-4611-ae55-e25562726d62',
    'the path to carcosa':  'ca208949-a47c-4454-9f74-f3ca630c7ed7',
    'the forgotten age':    '29e9861d-a9bb-4ac3-aced-a6feadde0f6f',
}


# octgn encoding of the five skill icons
skill_icon_symbols = {
    'Willpower': 'ά',
    'Intellect': 'έ',
    'Combat': 'ή',
    'Agility': 'ί',
    'Wild': 'ΰ',
}

octgn_symbol_map = {
    '[Willpower]': 'ά',
    '[Intellect]': 'έ',
    '[Combat]': 'ή',
    '[Agility]': 'ί',
    '[Wild]': 'ΰ',
    '[Action]': 'η',
    '[Reaction]': 'ι',
    '[Free]': 'θ',
    '[Guardian]': 'κ',
    '[Seeker]': 'λ',
    '[Rogue]': 'ν',
    '[Mystic]': 'μ',
    '[Survivor]': 'ξ',
    '[Skull]': 'α',
    '[Cultist]': 'β',
    '[Tablet]': 'γ',
    '[Elder Thing]': 'δ',
    '[Auto-fail]': 'ζ',
    '[Elder Sign]': 'ε',
    '[Investigators]': 'π',
}


octgn_scenario_sections = [ 'Act', 'Agenda', 'Location', 'Encounter', 'Setup',
                            'Special', 'Second Special']


class SetDataError(Exception):
    """Base class for exceptions in this module."""
    pass


# in-place prettyprint formatter
# from http://effbot.org/zone/element-lib.htm#prettyprint
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


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
    if (card['front']['data'].get('Subtype', '') == 'Basic Weakness'
            or card['front']['data']['Type'] in ('Asset', 'Skill', 'Event', 'Investigator')):
        return 'InvestigatorCard'
    elif card['front']['data']['Type'] in ('Scenario', 'Location', 'Treachery', 'Enemy'):
        return 'EncounterCard'
    elif card['front']['data']['Type'] in ('Act', 'Agenda'):
        return 'HorizCard'
    else:
        return ''


# convert arkhamset card text into OCTGN xml card text
def format_text_for_octgn(text):
    # TODO: handle any weird XML stuff?
    for k, v in octgn_symbol_map.items():
        text = text.replace(k, v)
    return text


def format_side_data_fields_for_octgn(side):
    for field in arkham_common.side_data_fields_with_possible_symbols:
        if field in side['data']:
            side['data'][field] = format_text_for_octgn(side['data'][field])


# convert skill icon info in cardgamedb format into OCTGN format (single string)
# delete original skill fields from side data dict
def make_skill_icons_string_for_side(side):
    icons_string = ''
    for skill, symbol in skill_icon_symbols.items():
        num_icons = int(side['data'].get(skill, 0))
        icons_string += (symbol * num_icons)
        """
        try:
            del side['data'][skill]
        except KeyError:
            pass
        """


    side['data']['Skill Icons'] = icons_string


def make_slot_strings_for_side(side):
    # TODO: handle double hand and arcane slots, handle weird stuff like flamethrower
    pass


def format_side_for_octgn(side):
    if side['data'].get('Type', '') in ['Asset', 'Skill', 'Event']:
        make_skill_icons_string_for_side(side)
    if side['data'].get('Type', '') == 'Asset':
        make_slot_strings_for_side(side)
    format_side_data_fields_for_octgn(side)
    del side['data']['Wild']


def format_card_for_octgn(card):
    format_side_for_octgn(card['front'])
    if arkham_common.is_double_sided(card):
        format_side_for_octgn(card['back'])


def card_to_xml(card):
    if 'id' not in card:
        card['id'] = uuid.uuid4()
    size = get_card_size(card)
    front_attrib = {'id': card['id'], 'name': card['front']['name'], 'size': size}
    front_root = ET.Element('card', front_attrib)

    format_card_for_octgn(card)

    ET.SubElement(front_root, 'property', {'name': 'Card Number', 'value': card['number']})
    ET.SubElement(front_root, 'property', {'name': 'Quantity', 'value': card['quantity']})
    if 'encounter_set' in card:
        ET.SubElement(front_root, 'property', {'name': 'Encounter Set', 'value': card['encounter_set']})
    for k, v in card['front']['data'].items():
        ET.SubElement(front_root, 'property', {'name': k, 'value': v})

    if arkham_common.is_double_sided(card):
        back_attrib = {'name': card['back']['name'], 'size': size, 'type': 'B'}
        back_root = ET.SubElement(front_root, 'alternate', back_attrib)
        if 'encounter_set' in card:
            ET.SubElement(back_root, 'property', {'name': 'Encounter Set', 'value': card['encounter_set']})
        for k, v in card['back']['data'].items():
            ET.SubElement(back_root, 'property', {'name': k, 'value': v})

    return front_root


# make set.xml file containing metadata on all cards
def create_set_xml(arkhamset):

    # TODO: figure out XML header? Or generate it with args to ET.write()?
    set_attrib = {
        'xmlns:noNamespaceSchemaLocation': 'CardSet.xsd',   # is this right?
        'name': arkhamset['name'],
        'id': arkhamset['id'],
        'gameId': game_id,
        'gameVersion': '1.0.0.0',
        'version': '1.0.0',
        'standalone': 'True',
    }
    set_root = ET.Element('set', set_attrib)
    cards = ET.SubElement(set_root, 'cards')
    for card in arkhamset['cards']:
        cards.append(card_to_xml(card))

    # TODO: handle exceptions or whatever
    indent(set_root)
    return set_root


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


def update_scenario_card_from_xml_tag(scenario_card, tag):
    scenario_card = scenario_card or {}
    scenario_card['id'] = scenario_card.get('id', '') or tag.attrib['id']
    scenario_card['name'] = scenario_card.get('name', '') or tag.attrib['name']
    scenario_card['number'] = scenario_card.get('number', '') or tag.find("./property[@name='Card Number']").attrib['value']
    scenario_card['quantity'] = scenario_card.get('quantity', '') or tag.find("./property[@name='Quantity']").attrib['value']
    scenario_card['encounter_set'] = scenario_card.get('encounter_set', '') or tag.find("./property[@name='Encounter Set']").attrib['value']
    return scenario_card

# Get a list of scenario_card objects corresponding to a given encounter set
# We don't care about recording the source of these cards because presumably
# the caller must already know it.
#       name: name of encounter set
#       root: root of xml tree describing the set which contains the given encounter set
def get_encounter_set(name, root):
    XPath_query_string = "./cards/card/property[@name='Encounter Set'][@value='{}']/..".format(name)
    cards = [update_scenario_card_from_xml_tag({}, tag) for tag in root.findall(XPath_query_string)]
    return cards


def create_xml_tag_from_scenario_card(card):
    card_attrib = {'qty': card['quantity'], 'id': card['id'], }
    card_tag = ET.Element('card', card_attrib)
    card_tag.text = card['name']
    return card_tag


# Given a card with possibly incomplete information, look up the rest if possible
#   require source set id and either card id or both card name and card number
def validate_card_fields(card, xml_root):
    if all([card.get(k, '') for k in ['id', 'name', 'number', 'quantity']]):
        return
    else:
        if card['id']: # find card based on id
            tag = xml_root.find("./cards/card[@id='{}']".format(card['id']))
        elif card['name'] and card['number']: # find card based on name and number
            tag = xml_root.find("./cards/card/property[@name='{}']/..".format(card['name']))
            # TODO: also check for number
        else:
            error_msg = "Badly formed card or encounter set in scenario {}:\n{}".format(scenario['name'], card)
            raise SetDataError(error_msg)

        update_scenario_card_from_xml_tag(card, tag)


def validate_source_field(card, default):
    if 'source' not in card or not card['source']:
        card['source'] = default
    else:
        card['source'] = card['source'].lower().strip()
        if card['source'] in ('core set', 'core', 'coreset'):
            card['source'] = campaign_ids['core set']
        elif card['source'] == 'campaign':
            try:
                card['source'] = campaign_ids[scenario['campaign'].lower()]
            except KeyError:
                error_msg = 'Campaign {} is not listed in known campaigns.'.format(scenario['campaign'])
                raise SetDataError(error_msg)
        elif not re.match('^[0-9a-f]{8}(?:-?[0-9a-f]{4}){3}-?[0-9a-z]{12}$', card['source']):
            error_msg = 'Invalid source field {}. Must be a UUID, "Campaign", or "Core Set"'.format(card['source'])
            raise SetDataError(error_msg)


# TODO: lookup card IDs for existing sets
# TODO: handle encounter sets
def create_scenario_xml(scenario, set_id):
    deck_attrib = {'game': game_id, 'sleeveid': '0'}
    deck_root = ET.Element('deck', deck_attrib)

    section_roots = {}
    for section in ['Investigator', 'Asset', 'Event', 'Skill', 'Weakness',
                    'Sideboard', 'Basic Weaknesses']:
        ET.SubElement(deck_root, 'section', {'name': section, 'shared': 'False'})
    for section in octgn_scenario_sections + ['Chaos Bag']:
        section_roots[section] = ET.SubElement(
                deck_root, 'section', {'name': section, 'shared': 'True'})

    # add SubElements for the interesting sections and sort cards from those sections by source
    cards_by_source = {}
    for section in octgn_scenario_sections:
        section_cards = scenario.get(section, [])
        for card in section_cards:
            validate_source_field(card, set_id)
            source = card['source']
            cards_by_source[source] = cards_by_source.get(source, {})
            cards_by_source[source][section] = cards_by_source[source].get(section, [])
            cards_by_source[source][section].append(card)

    for source in cards_by_source:
        path = "GameDatabase/{}/Sets/{}/set.xml".format(game_id, source)
        source_root = ET.parse(path).getroot()

        for section, cards in cards_by_source[source].items():
            while cards:
                card = cards.pop()
                if card['encounter_set'] and not any([
                        card['name'], card.get('id', ''), card.get('number', ''), card.get('quantity', '')]):
                    encounter_set = get_encounter_set(card['encounter_set'], source_root)
                    if not encounter_set:
                        error_msg = "Couldn't find any cards for encounter set {} in source {}".format(card['encounter_set'], source)
                        raise SheetDataError(error_msg)
                    for c in encounter_set:
                        c.update({'source': source, 'section': section})
                        cards.append(c)
                else:
                    validate_card_fields(card, source_root)
                    section_roots[section].append(create_xml_tag_from_scenario_card(card))


    notes = ET.SubElement(deck_root, 'notes')
    notes.text = "<![CDATA[]]>"                 # is this right?

    indent(deck_root)
    return deck_root


def create_octgn_package(arkhamset):

    if 'id' not in arkhamset or not arkhamset['id']:
        arkhamset['id'] = uuid.uuid4()

    # create xml file containing all cards in set
    set_dir = "GameDatabase/{}/Sets/{}/".format(game_id, arkhamset['id'])
    try:
        os.makedirs(set_dir)
    except FileExistsError:
        pass
    set_path = set_dir + 'set.xml'
    set_root = create_set_xml(arkhamset)
    xml_tree = ET.ElementTree(set_root)
    xml_tree.write(set_path, encoding='UTF-8', xml_declaration=True)
    print("created set XML file {}.".format(set_path))

    # create xml file for each scenario with cards needed for play
    #gamedb_decks_path = "GameDatabase/{}/Decks/".format(game_id)
    decks_path = "Decks/Arkham Horror - The Card Game/"
    for scenario in arkhamset.get('scenarios', []):
        campaign_path = "{}/{} - {}".format(
                decks_path, scenario['campaign_code'], scenario['campaign'])
        try:
            os.makedirs(campaign_path)
        except FileExistsError:
            pass
        scenario_string = "{} - {}".format(scenario['number'], scenario['name'])
        scenario_file_path = "{}/{}.o8d".format(campaign_path, scenario_string)

        scenario_root = create_scenario_xml(scenario, arkhamset['id'])
        scenario_xml_tree = ET.ElementTree(scenario_root)
        scenario_xml_tree.write(scenario_file_path, encoding='UTF-8', xml_declaration=True)
        print("created scenario file {}.".format(scenario_file_path))

    # create image files for cards
    imagedb_path = "ImageDatabase/{}/Sets/{}/Cards/".format(game_id, arkhamset['id'])
    try:
        os.makedirs(imagedb_path)
    except FileExistsError:
        pass
    num = create_card_image_files(arkhamset, imagedb_path)
    print("created {} card image files in {}.".format(num, imagedb_path))

    # TODO: zip directory tree at the end?
    # TODO: return path to created directory or archive
    return None


if __name__ == '__main__':
    pass
