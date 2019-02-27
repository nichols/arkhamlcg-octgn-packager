# TODO: add module description

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

set_fields = [      # types                 cardgamedb?
  'id',
  'name',           #                       yes
  'type',           # set_type_enum
  'campaign',
  'campaign_code',
  'cards',          # [card]
  'scenarios',      # [scenario]
]

card_fields = [     # types                 cardgamedb?
  'id',
  'mini',           # bool default:False
  'number',         #                       yes
  'quantity',       # int default:1         yes
  'encounter_set',
  'front',          # side
  'back',           # side
]


side_fields = [     # type                  cardgamedb?
  'name',           #                       front only
  'image_url'       #                       yes
  'data'            # side_data
]


scenario_fields = [ # type                  cardgamedb?
  'campaign',
  'number',
  'name',
  'agendas'         # [scenario_card]
  'act',            # [scenario_card]
  'location',       # [scenario_card]
  'encounter',      # [scenario_card]
  'setup',          # [scenario_card]
]

scenario_card_fields = [
  'name',
  'number',
  'id'
  'set_id',
  'quantity',
]
"""

# fields that can be dumped directly into the OCTGN xml file
side_data_fields = [
  'Subtitle',
  'Type',
  'Subtype',
  'Traits',
  'Text',
  'Flavor Text',
  'Health',         # Health for investigators, assets, and enemies
  'Sanity',
  'Class',          # Faction for player cards, "Mythos" for scenario cards
  'Level',          # Level for player cards, agenda/act number for agendas/acts
  'Cost',
  'Willpower',      # Skill for investigators, skill icon on other player cards
  'Intellect',      # Skill for investigators, skill icon on other player cards
  'Combat',         # Skill for investigators, skill icon on other player cards, fight difficulty for enemies
  'Agility',        # Skill for investigators, skill icon on other player cards, evade difficulty for enemies
  'Wild',
  'Slot',
  'Unique',
  'Shroud',
  'Clues',
  'Doom',
  'Damage',
  'Horror',
  'Victory Points',
]
# side_data fields we can get from cardgamedb:
# 'Type', 'Class', 'Health', 'Sanity', 'Willpower', 'Intellect', 'Combat',
# 'Agility', 'Traits', 'Text', 'Flavor Text'
# Note some of these fields are only given for some types of cards
# For instance, cardgamedb doesn't list combat and agility for enemies
# Also, for back sides only the text is given by cardgamedb. No other fields.

# side_data fields supported by OCTGN but not provided by cardgamedb
# 'Subtype', 'Encounter Set', 'Unique', 'Shroud', 'Clues', 'Doom', 'Victory Points'
# these can be entered manually in a spreadsheet


def is_double_sided(card):
    return 'back' in card


symbol_per_investigator_cardgamedb = '\udb88\udd83'
symbol_per_investigator_octgn = 'π'


def load_set(json_file_path):
    with open(json_file_path, 'r') as json_file:
        arkhamset = json.load(json_file)
    return arkhamset


def create_set_file(arkhamset, path=None):
    if path is None:
        json_file_path = arkhamset['name'] + '.json'
    with open(json_file_path, 'w') as json_file:
        json.dump(arkhamset, json_file)
    return json_file_path
