# TODO: add module description
# TODO: add minicard automatically whenever we add an investigator card

import uuid
import os
import re
import xml.etree.ElementTree as ET
import arkham_lib

class SetDataError(Exception):
    """Base class for exceptions in this module."""
    pass

skill_icon_symbols = {
    'Willpower': 'ά',
    'Intellect': 'έ',
    'Combat': 'ή',
    'Agility': 'ί',
    'Wild': 'ΰ',
}
action_symbols = {
    '[Action]': 'η',
    '[Reaction]': 'ι',
    '[Free]': 'θ',
}
class_symbols = {
    '[Guardian]': 'κ',
    '[Seeker]': 'λ',
    '[Rogue]': 'ν',
    '[Mystic]': 'μ',
    '[Survivor]': 'ξ',
}
chaos_token_symbols = {
    '[Skull]': 'α',
    '[Cultist]': 'β',
    '[Tablet]': 'γ',
    '[Elder Thing]': 'δ',
    '[Auto-fail]': 'ζ',
    '[Elder Sign]': 'ε',
}
other_symbols = {
    '[Investigators]': 'π',
}


_card_sizes = frozenset(
    ['InvestigatorCard', 'HorizCard', 'EncounterCard', 'MiniCard'])

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


def card_size(card):
    if card.front.type == 'Investigator':
        return 'InvestigatorCard'
    elif (card.front.type in ('Scenario', 'Location', 'Treachery', 'Enemy')
          and card.front.subtype != 'Basic Weakness'):
        return 'EncounterCard'
    elif card.front.type in ('Act', 'Agenda'):
        return 'HorizCard'
    else:
        return None


# convert arkhamset card text into OCTGN xml card text
def format_text_for_octgn(text):
    # TODO: handle any weird XML stuff?
    for k, v in octgn_symbol_map.items():
        text = text.replace(k, v)
    return text


# create OCTGN format skill icons field (single string)
def format_skill_icons_for_side(side):
    icons_string = ''
    for skill, symbol in skill_icon_symbols.items():
        num_icons = int(side['data'].get(skill, "0"))
        icons_string += (symbol * num_icons)

    side['data']['Skill Icons'] = icons_string


def card_to_xml_element(card):
    size = get_card_size(card)
    front_attrib = dict(
        id=card.id, name=card.front.name, size=size)
    front_root = ET.Element('card', front_attrib)

    ET.SubElement(front_root, 'property', dict(
        name='Card Number', value=card.set_number))
    ET.SubElement(front_root, 'property', dict(
        name='Quantity', value=card.quantity))
    if card.encounter_set:
        ET.SubElement(front_root, 'property', dict(
            name='Encounter Set', value=card.encounter_set))
    for k, v in card['front']['data'].items():
        ET.SubElement(front_root, 'property', {'name': k, 'value': v})

    if card.back:
        back_attrib = dict(name=card.back.title, type='B', size=size)
        back_root = ET.SubElement(front_root, 'alternate', back_attrib)
        if 'encounter_set' in card:
            ET.SubElement(back_root, 'property', {'name': 'Encounter Set', 'value': card['encounter_set']})
        for k, v in card['back']['data'].items():
            ET.SubElement(back_root, 'property', {'name': k, 'value': v})

    return front_root


# create XML tree containing metadata on all cards in this set
def create_set_xml(arkhamset):
    # TODO: figure out XML header? Or generate it with args to ET.write()?
    set_attrib = {
        'xmlns:noNamespaceSchemaLocation': 'CardSet.xsd',   # is this right?
        'name': arkhamset.name,
        'id': arkhamset.id,
        'gameId': constants.octgn_game_id,
        'gameVersion': '1.0.0.0',
        'version': '1.0.0',
        'standalone': 'True',
    }
    set_root = ET.Element('set', set_attrib)
    cards_root = ET.SubElement(set_root, 'cards')
    cards_root.extend((card_to_xml_element(card) for card in arkhamset.cards))

    return set_root


def create_set_data(arkhamset):
    # create xml file containing all cards in set
    set_dir = "GameDatabase/{}/Sets/{}/".format(arkham_common.octgn_game_id, arkhamset['id'])
    try:
        os.makedirs(set_dir)
    except FileExistsError:
        pass
    set_path = set_dir + 'set.xml'
    set_root = create_set_xml(arkhamset)
    indent(set_root)
    xml_tree = ET.ElementTree(set_root)
    xml_tree.write(set_path, encoding='UTF-8', xml_declaration=True)
    print("created set XML file {}.".format(set_path))

    return set_path
