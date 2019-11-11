# TODO: add module description
# TODO: add minicard automatically whenever we add an investigator card

import uuid
import os
import re
import xml.etree.ElementTree as ET
import arkham_common


# directories to search to find existing sets.
# If you have OCTGN installed in windows, this is probably
# <My Documents>/OCTGN/GameDatabase/a6d114c7-2e2a-4896-ad8c-0330605c90bf/Sets
octgn_sets_directories = [
    'Sets',         # for development
    os.path.join(
        'GameDatabase', arkham_common.octgn_game_id, 'Sets'),
]

uuid_regex_pattern = '^[0-9a-f]{8}(?:-?[0-9a-f]{4}){3}-?[0-9a-z]{12}$'

campaign_ids = {
    'core set':             '0000f984-d06f-44cb-bf1c-d66a620acad8',
    'markers and tokens':   '0ab2f6e6-efd6-434e-95aa-ba10c3cf8ccd',
    'the dunwich legacy':   'dfa9b3bf-58f2-4611-ae55-e25562726d62',
    'the path to carcosa':  'ca208949-a47c-4454-9f74-f3ca630c7ed7',
    'the forgotten age':    '29e9861d-a9bb-4ac3-aced-a6feadde0f6f',
    'the circle undone':    '44513a54-7bd1-4366-a8a0-f4de20be510d',
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
    '[per investigator]': 'π',
    '': '',
}

octgn_symbol_map.update(skill_icon_symbols)

octgn_scenario_sections = [
    'Act',
    'Agenda',
    'Location',
    'Encounter',
    'Setup',
    'Special',
    'Second Special',
]

octgn_forbidden_side_fields = [
    'Wild',
]


# things people might enter in the source field that we want to interpret
source_alias = {
    'core set': ['core', 'coreset', 'core_set'],
    'campaign': ['campaign'],
    'markers and tokens': [
        'markers and tokens', 'markers', 'tokens', 'markersandtokens',
        'markers_and_tokens', 'tokens and markers', 'tokens_and_markers',
        'markers tokens', 'tokens markers'],
}


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


def get_card_size(card):
    # possible values: 'InvestigatorCard', 'HorizCard', 'EncounterCard', 'MiniCard'
    cardtype = card['front']['data']['Type']
    if cardtype == 'Investigator':
        return 'InvestigatorCard'
    elif (cardtype in ('Scenario', 'Location', 'Treachery', 'Enemy')
            and card['front']['data'].get('Subtype', '') != 'Basic Weakness'):
        return 'EncounterCard'
    elif cardtype in ('Act', 'Agenda'):
        return 'HorizCard'
    else:
        return None


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


# create OCTGN format skill icons field (single string)
def format_skill_icons_for_side(side):
    icons_string = ''
    for skill, symbol in skill_icon_symbols.items():
        num_icons = int(side['data'].get(skill, "0"))
        icons_string += (symbol * num_icons)

    side['data']['Skill Icons'] = icons_string


def format_slot_strings_for_side(side):
    # TODO: handle double hand and arcane slots, handle weird stuff like
    #       flamethrower and enchanted blade
    pass


def format_side_for_octgn(side):
    if side['data'].get('Type', '') in ['Asset', 'Skill', 'Event']:
        format_skill_icons_for_side(side)
    if side['data'].get('Type', '') == 'Asset':
        format_slot_strings_for_side(side)
    format_side_data_fields_for_octgn(side)

    for forbidden_field in octgn_forbidden_side_fields:
        if forbidden_field in side['data']:
            del side['data'][forbidden_field]


def format_card_for_octgn(card):
    if 'id' not in card:
        card['id'] = uuid.uuid4()

    format_side_for_octgn(card['front'])
    if arkham_common.is_double_sided(card):
        format_side_for_octgn(card['back'])

    size = get_card_size(card)
    if size:
        card['size'] = size


def card_to_xml_element(card):
    format_card_for_octgn(card)

    front_attrib = {'id': card['id'], 'name': card['front']['name']}
    if card.get('size', ''):
        front_attrib['size'] = card['size']
    front_root = ET.Element('card', front_attrib)

    ET.SubElement(front_root, 'property', {'name': 'Card Number', 'value': card['number']})
    ET.SubElement(front_root, 'property', {'name': 'Quantity', 'value': card['quantity']})
    if 'encounter_set' in card:
        ET.SubElement(front_root, 'property', {'name': 'Encounter Set', 'value': card['encounter_set']})
    for k, v in card['front']['data'].items():
        ET.SubElement(front_root, 'property', {'name': k, 'value': v})

    if arkham_common.is_double_sided(card):
        back_attrib = {'name': card['back']['name'], 'type': 'B'}
        if card.get('size', ''):
            back_attrib['size'] = card['size']
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
        'name': arkhamset['name'],
        'id': arkhamset['id'],
        'gameId': arkham_common.octgn_game_id,
        'gameVersion': '1.0.0.0',
        'version': '1.0.0',
    }
    set_root = ET.Element('set', set_attrib)
    cards_root = ET.SubElement(set_root, 'cards')
    for card in arkhamset['cards']:
        cards_root.append(card_to_xml_element(card))

    indent(set_root)
    return set_root

# Read data from an XML element describing a card and use it to fill in missing
# fields for a scenario card.
def update_scenario_card_from_xml_element(scenario_card, tag):
    card_from_tag = {
        'id': tag.attrib['id'],
        'name': tag.attrib['name'],
    }
    find_number = tag.find("./property[@name='Card Number']")
    if find_number is not None:
        card_from_tag['number'] = find_number.attrib['value']

    find_quantity = tag.find("./property[@name='Quantity']")
    if find_quantity is not None:
        card_from_tag['quantity'] = find_quantity.attrib['value']

    find_encounter_set = tag.find("./property[@name='Encounter Set']")
    if find_encounter_set is not None:
        card_from_tag['encounter_set'] = find_encounter_set.attrib['value']

    scenario_card.update(card_from_tag)

    # We should now have values for all of these fields.
    needed_fields = {'id', 'name', 'number', 'quantity', 'encounter_set'}
    missing_fields = needed_fields.difference(set(scenario_card))
    if missing_fields:
        error_msg = (
            "Missing fields after loading card data XML: {}\n".format(missing_fields)
            + scenario_card)
        raise SetDataError(error_msg)

    return scenario_card


# Get a list of scenario_card objects corresponding to a given encounter set
# We don't care about recording the source of these cards because presumably
# the caller must already know it.
#       name: name of encounter set
#       root: root of xml tree of the set which contains given encounter set
def get_encounter_set(name, root):
    XPath_query_string = (
        "./cards/card/property[@name='Encounter Set'][@value='{}']/.."
        .format(name))
    cards = [update_scenario_card_from_xml_tag({}, tag)
                for tag in root.findall(XPath_query_string)]
    return cards


# Create an XML element for a scenario card. This XML element will go into an
# .o8d deck file.
def create_xml_element_for_scenario_card(card):
    card_attrib = {
        'id': card['id'],
        'qty': card['quantity'],
    }
    card_tag = ET.Element('card', card_attrib, text=card['name'])
    return card_tag


# Given a card with possibly incomplete information, find the corresponding
# XML element in that card's set's XML tree. Card must either have an ID or both
# name and number.
def find_xml_element_for_scenario_card(card, xml_root):
    if card.get('id', ''): # find card based on id
        return xml_root.find("./cards/card[@id='{}']".format(card['id']))
    elif card['name'] and card['number']: # find card based on name and number
        return xml_root.find(
            "./cards/card/property[@name='{}' and @number='{}']/.."
            .format(card['name'], card['number']))
    else:
        error_msg = "Not enough fields to identify card: {}".format(card)
        raise SetDataError(error_msg)


# If source field is given as the name of a campaign or "Core Set" etc, look up
# the UUID of the source set. 'card' is actually a row in the Scenarios sheet,
# it could be an encounter set or token instead of a card.
def validate_source_field(card, default):
    card['source'] = card.get('source', '').lower().strip() or default

    if card['source'] in campaign_ids:
        card['source'] = campaign_ids[card['source']]
    elif not re.match(uuid_regex_pattern, card['source']):
        error_msg = (
            'Invalid source field: {}.'.format(card.get('source', ''))
            + 'Must be a UUID, "Markers and Tokens", "Core Set", empty (""),'
            + ' or name of a campaign.')
        raise SetDataError(error_msg)


def get_existing_set_xml_path(source):
    for dir in octgn_sets_directories:
        path = os.path.join(dir, source, "set.xml")
        if os.path.exists(path):
            return path
    error_msg = "Couldn't locate existing set with uuid {}".format(source)
    raise SetDataError(error_msg)


def scenario_card_entry_is_encounter_set(card):
    return (
        card.get('encounter_set', '')
        and not any([
            card['name'], card.get('id', ''), card.get('number', ''),
            card.get('quantity', '')])
    )


def scenario_card_entry_is_token(card):
    return (card['source'] in (
        'markers and tokens', campaign_ids['markers and tokens']))


def get_token(card, xml_root):
    element = xml_root.find(
        "./cards/card/property[@name='{}']/..".format(card['name']))
    if not element:
        error_msg = "Couldn't find this in the tokens list: {}".format(card)
        raise SetDataError(error_msg)
    elif element.attrib['size'] != 'ChaosToken':
        error_msg = "It looks like this is not a token: {}".format(card)
        raise SetDataError(error_msg)

    #card['id'] = element.attrib['id']
    return card


def create_scenario_xml(scenario, set_id):
    deck_attrib = {'game': arkham_common.octgn_game_id, 'sleeveid': '0'}
    deck_root = ET.Element('deck', deck_attrib)

    # create roots for each section with appropriate attribs
    section_roots = {}
    for section in ['Investigator', 'Asset', 'Event', 'Skill', 'Weakness',
                    'Sideboard', 'Basic Weaknesses']:
        ET.SubElement(
            deck_root, 'section', {'name': section, 'shared': 'False'})
    for section in octgn_scenario_sections + ['Chaos Bag']:
        section_roots[section] = ET.SubElement(
            deck_root, 'section', {'name': section, 'shared': 'True'})

    # Accumulate cards from all sections and divide by source.
    cards_by_source = {}
    for section in octgn_scenario_sections:
        section_cards = scenario.get(section, [])
        for card in section_cards:
            validate_source_field(card, set_id)
            source = card['source']

            # add to cards_by_source[source][section], adding keys as needed
            cards_by_source[source] = cards_by_source.get(source, {})
            cards_by_source[source][section] = cards_by_source[source].get(section, [])
            cards_by_source[source][section].append(card)

    # Now we can do one lookup pass per source.
    for source in cards_by_source:

        try:
            path = get_existing_set_xml_path(source)
            source_root = ET.parse(path).getroot()
        except ET.ParseError:
            print("Couldn't parse XML for source {}".format(source))
            raise

        for section, cards in cards_by_source[source].items():
            while cards:
                card = cards.pop()
                if scenario_card_entry_is_encounter_set(card):
                    encounter_set = get_encounter_set(
                        card['encounter_set'], source_root)
                    if not encounter_set:
                        error_msg = (
                            "Couldn't find any cards for encounter set {}"
                            + " in source {}"
                        ).format(card['encounter_set'], source)
                        raise SetDataError(error_msg)
                    for encounter_card in encounter_set:
                        encounter_card.update(
                            {'source': source, 'section': section})
                        cards.append(encounter_card)
                elif scenario_card_entry_is_token(card):
                    section_roots[section].append(
                        create_xml_element_for_scenario_card(card))
                else:
                    if not all(
                        [card.get(k, '')
                        for k in ['id', 'name', 'number', 'quantity']]
                    ):
                        element = find_xml_element_for_scenario_card(card,
                            source_root)
                        update_scenario_card_from_xml_element(card, element)

                    section_roots[section].append(
                        create_xml_element_for_scenario_card(card))

    # add stuff to the end of the scenario XML file
    notes = ET.SubElement(deck_root, 'notes')
    notes.text = "<![CDATA[]]>"                 # is this right?

    indent(deck_root)
    return deck_root


def create_octgn_data(arkhamset):
    if 'id' not in arkhamset or not arkhamset['id']:
        arkhamset['id'] = uuid.uuid4()

    # create xml file containing all cards in set
    set_dir = os.path.join(
        "GameDatabase", arkham_common.octgn_game_id, "Sets", arkhamset['id'])
    try:
        os.makedirs(set_dir)
    except FileExistsError:
        pass
    set_filename = 'set.xml'
    set_path = os.path.join(set_dir, set_filename)
    set_root = create_set_xml(arkhamset)
    xml_tree = ET.ElementTree(set_root)
    xml_tree.write(set_path, encoding='UTF-8', xml_declaration=True)
    print("created set XML file {}.".format(set_path))

    # create xml file for each scenario with cards needed for play
    #gamedb_decks_path = "GameDatabase/{}/Decks/".format(game_id)
    game_path = os.path.join("Decks", "Arkham Horror - The Card Game")
    for scenario in arkhamset.get('scenarios', []):
        campaign_dir = "{} - {}".format(
                scenario['campaign_code'], scenario['campaign'])
        campaign_path = os.path.join(game_path, campaign_dir)
        try:
            os.makedirs(campaign_path)
        except FileExistsError:
            pass
        scenario_filename = "{} - {}.o8d".format(
            scenario['number'], scenario['name'])
        scenario_path = os.path.join(campaign_path, scenario_filename)

        scenario_root = create_scenario_xml(scenario, arkhamset['id'])
        scenario_xml_tree = ET.ElementTree(scenario_root)
        scenario_xml_tree.write(
            scenario_path, encoding='UTF-8', xml_declaration=True)
        print("created scenario file {}.".format(scenario_path))

    return (set_path, scenario_path)
