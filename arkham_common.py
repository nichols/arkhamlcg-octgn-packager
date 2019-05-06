# common functions used across the whole package

import re
import json

"""
# objects (set, card, scenario, etc) are stored as simple dicts for convenience.

set_type_enum = [
  'Core Set',
  'Expansion',
  'Mythos Pack',
  'Scenario Pack',
  'Other',
]

set = {
  'id': string,             # uuid
  'name': string,           # from cardgamedb
  'type': string            # set_type_enum
  'cards': [card],
  'scenarios': [scenario],
}

card = {
  'id': string,             # uuid
  'number': string,         # from cardgamedb
  'quantity': string,       # from cardgamedb; default:1
  'encounter_set': string,
  'front': side,
  'back': side,
}


side = {
  'name': string,           # from cardgamedb (front only)
  'image_url': string       # from cardgamedb
  'data': side_data
]


scenario = {
  'number': string,
  'name': string,
  'campaign': string,
  'campaign_code': string,
  'Agendas': [scenario_card],
  'Act': [scenario_card],
  'Location': [scenario_card],
  'Encounter': [scenario_card],
  'Setup': [scenario_card],
  'Special': [scenario_card],
  'Second Special': [scenario_card],
}

scenario_card = {
  'id': string              # uuid,
  'name': string,
  'number': string,
  'encounter_set': string,
  'quantity': string,
  'source': string,         # uuid
}
"""

side_data = [       # all of these fields are strings
  'Subtitle',
  'Type',
  'Subtype',
  'Traits',
  'Text',
  'Health',         # Health for investigators, assets, and enemies
  'Sanity',         # Sanity for investigators and assets
  'Class',          # Faction for player cards, "Mythos" for scenario cards
  'Level',          # Level for player cards, agenda/act number for agendas/acts
  'Cost',
  'Willpower',      # Skill for investigators, skill icon on other player cards
  'Intellect',      # Skill for investigators, skill icon on other player cards
  'Combat',         # Skill for investigators, skill icon on other player cards, fight difficulty for enemies
  'Agility',        # Skill for investigators, skill icon on other player cards, evade difficulty for enemies
  'Wild',           # Skill icon for player cards. Not used in OCTGN for some reason
  'Slot',
  'Unique',
  'Shroud',
  'Clues',
  'Doom',
  'Damage',
  'Horror',
  'Victory Points',
]

# these are the fields which may contain special symbols that are represented
# differently in cardgamedb and OCTGN
side_data_fields_with_possible_symbols = [
  'Text',
  'Health',         # Health for investigators, assets, and enemies
  'Clues',
  'Doom',
]
# side_data fields we can get from cardgamedb:
# 'Type', 'Class', 'Health', 'Sanity', 'Willpower', 'Intellect', 'Combat',
# 'Agility', 'Traits', 'Text', 'Flavor Text'
# Note some of these fields are only given for some types of cards
# For instance, cardgamedb doesn't list combat and agility for enemies
# Also, for back sides only the text is given by cardgamedb. No other fields.

# side_data fields supported by OCTGN but not provided by cardgamedb
# 'Subtype', 'Encounter Set', 'Unique', 'Shroud', 'Clues', 'Doom', 'Victory Points'
# these can be entered manually the spreadsheet


octgn_game_id = 'a6d114c7-2e2a-4896-ad8c-0330605c90bf'


def is_double_sided(card):
    return 'back' in card


# remove trailing a or b from number, return number and face
def get_number_and_face(number):
    m = re.match('^(\d+)([ab]?)$', number)
    if not m:
        raise ValueError
    number = m.group(1)
    if m.group(2) == 'a':
        face = 'front'
    elif m.group(2) == 'b':
        face = 'back'
    else:
        face = ''

    return number, face


# We want to sort first by number and then by a/b face indicator.
# This would be easy to express as a binary comparison operator, but it's
# annoying to do as a key unary operator.
def card_number_sort_key(card):
    number, face = get_number_and_face(card.get('number', '999'))
    face = ord(face) if face else 0
    return 100*int(number) + face


def load_set(json_file_path):
    with open(json_file_path, 'r') as json_file:
        arkhamset = json.load(json_file)
    return arkhamset


def create_set_file(arkhamset, json_file_path=None):
    if json_file_path is None:
        json_file_path = arkhamset['name'] + '.json'
    with open(json_file_path, 'w') as json_file:
        json.dump(arkhamset, json_file)
    return json_file_path
