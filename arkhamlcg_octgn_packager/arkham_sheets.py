# Module for reading/writing an Arkham Horror LCG set object (as defined in
# arkham_common) to/from a Google Sheets spreadsheet. This provides an easy
# way to enter missing data.

import re
import uuid
import pickle
import arkham_lib
import sheets

sheet_template_filename = 'template.pickle'

class SheetDataError(Exception):
    """Base class for exceptions in this module."""
    pass

#
# Methods for writing an arkham set to a spreadsheet
#
"""

def fill_set_info_sheet(service, spreadsheet_id, arkhamset):
    range = 'Set!B2:B6'
    value_input_option = 'USER_ENTERED'
    column = [arkhamset.get('id', ''), arkhamset['name'], '']
    body = {
        'range': range,
        'values': [column],
        'majorDimension': 'COLUMNS',
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption=value_input_option, body=body).execute()


def make_row_for_card_side(card, face):
    number = card['number']
    if face == 'front':
        number += 'a'
    elif face == 'back':
        number += 'b'
    else:
        face = 'front'
    row = [ card[face]['name'],
            number,
            card['id'],
            card[face]['image_url'],
            card.get('quantity', ''),
            card.get('encounter_set', ''),
    ]
    row += [card[face]['data'].get(f, '') for f in arkham_common.side_data]
    return row


def fill_cards_sheet(service, spreadsheet_id, arkhamset):
    rows = []
    arkhamset['cards'].sort(key=arkham_common.card_number_sort_key)
    for card in arkhamset['cards']:
        if 'id' not in card or not card['id']:
            card['id'] = str(uuid.uuid4())

        if arkham_common.is_double_sided(card):
            new_rows = [make_row_for_card_side(card, 'front'),
                        make_row_for_card_side(card, 'back')]
        else:
            new_rows = [make_row_for_card_side(card, '')]
        rows.extend(new_rows)

    range = "Cards!A2:AD{}".format(1 + len(rows))
    value_input_option = 'USER_ENTERED'
    body = {
        'range': range,
        'values': rows,
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption=value_input_option, body=body).execute()


# We can pre-fill the scenario sheet even though we don't know the name of the
# scenario(s) or the setup instructions. We'll just print all the scenario cards
# from this set and let the user correct any errors.
def fill_scenario_sheet_guess(service, spreadsheet_id, arkhamset):
    section_names = ['Act', 'Agenda', 'Location', 'Encounter', 'Setup',
                    'Special', 'Second Special']
    sections = {s: [] for s in section_names}

    # this is just a best guess, it's probably not right for all of these cards
    for card in arkhamset['cards']:
        type = card['front']['data'].get('Type', '')
        if type in ['Act', 'Agenda', 'Location']:
            sections[type].append(card)
        elif type in ('Treachery', 'Enemy'):
            sections['Encounter'].append(card)
        elif (  type in ('Scenario', 'Story')
                or card['front']['data'].get('Class', '')
                not in ('Guardian', 'Seeker', 'Rogue', 'Mystic', 'Survivor',
                        'Neutral')):
            sections['Setup'].append(card)

    rows = []
    for s in section_names:
        if sections[s]:
            new_rows = [
                ['', card['id'], card['front']['name'], card['number'],
                        card.get('encounter_set', '')]
                for card in sections[s]
            ]
            new_rows[0][0] = s
            rows.extend(new_rows)

    range = "Scenarios!E2:I{}".format(1 + len(rows))
    value_input_option = 'USER_ENTERED'
    body = {
        'range': range,
        'values': rows,
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption=value_input_option, body=body).execute()


def create_spreadsheet_for_set(arkhamset):
    if 'id' not in arkhamset:
        arkhamset['id'] = str(uuid.uuid4())

    service = get_sheets_api_service()

    print('Creating template sheet... ', end='')
    with open(sheet_template_filename, 'rb') as sheet_template_file:
        spreadsheet = pickle.load(sheet_template_file)

    spreadsheet['properties']['title'] = 'Arkham Horror LCG: {}'.format(
        arkhamset['name'])
    spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    print('Done, ID = {}.'.format(spreadsheet_id))

    print('Filling set info sheet... ', end='')
    fill_set_info_sheet(service, spreadsheet_id, arkhamset)
    print('Done.')

    print('Filling cards sheet... ', end='')
    fill_cards_sheet(service, spreadsheet_id, arkhamset)
    print('Done.')

    print('Filling scenario sheet... ', end='')
    fill_scenario_sheet_guess(service, spreadsheet_id, arkhamset)
    print('Done.')

    return spreadsheet.get('spreadsheetUrl')


#
# Methods for reading arkham set object from a spreadsheet
#

def read_set_info_sheet(sheet):
    rows = sheet['data'][0]['rowData'][1:]

    try:
        column = [sheets.get_string_from_cell(row['values'][1]) for row in rows]
        arkhamset = dict(zip(['id', 'name', 'type'], column))
    except IndexError:
        raise SheetDataError

    if not arkhamset['name']:
        raise SheetDataError

    return arkhamset


def read_cards_sheet(sheet):
    rows = sheet['data'][0]['rowData'][1:]

    incomplete_cards = {}
    cards = []

    for row in rows:
        name, number, id, image_url, quantity, encounter_set, *fields = sheets.read_row(row)
        if not name or not number:
            continue

        try:
            number, face = arkham_common.get_number_and_face(number)
        except ValueError:
            error_msg = "couldn't read number {}".format(number)
            raise SheetDataError(error_msg)

        card = {
            'id': id,
            'number': number,
            'quantity': quantity,
        }
        if encounter_set:
            card['encounter_set'] = encounter_set

        side_data = {}
        # only add non-blank fields to the data object
        for i, field in enumerate(arkham_common.side_data):
            try:
                if fields[i]:
                    side_data[field] = fields[i]
            except IndexError:
                print("card name {}, number {}, field = {}, i {}".format(name, number, field, i))
                print("fields: {}".format(fields))
                print("len(fields) = {}".format(len(fields)))
                raise

        side = {'name': name, 'image_url': image_url, 'data': side_data}

        if face:
            if number in incomplete_cards:
                if face in incomplete_cards[number]:
                    error_msg = (
                        'found two sides labeled "{}" for card number {}'.format(
                        face, number))
                    raise SheetDataError(error_msg)
                incomplete_cards[number][face] = side
                cards.append(incomplete_cards[number])
                del incomplete_cards[number]
            else:
                card[face] = side
                incomplete_cards[number] = card
        else:
            card['front'] = side
            cards.append(card)

    return cards


def read_scenarios_sheet(sheet):
    rows = map(sheets.read_row, sheet['data'][0]['rowData'][1:])

    scenario_dict = {}

    # fields describing the scenario carry over from previous row if blank
    last = [''] * 5

    for row in rows:
        if not any(row):
            continue
        try:
            for i in range(5):
                row[i] = row[i] or last[i]
            last = row[:5]

            name = row[3]
            section = row[4]

            card_fields = dict(zip(
                ['id', 'name', 'number', 'encounter_set', 'quantity', 'source'],
                row[5:11]
            ))
            if not card_fields['quantity'] and section in ('Act', 'Agenda', 'Location'):
                card_fields['quantity'] = '1'
            scenario = dict(zip(
                ['campaign_code', 'campaign', 'number', 'name', section],
                row[:4] + [[card_fields]]
            ))
        except IndexError:
            raise SheetDataError

        # merge this card into the existing list of scenarios
        if name not in scenario_dict:
            scenario_dict[name] = scenario
        elif section not in scenario_dict[name]:
            scenario_dict[name][section] = scenario[section]
        else:
            scenario_dict[name][section].extend(scenario[section])

    scenarios = list(scenario_dict.values())
    return scenarios


def read_set(url, get_scenarios=True):
    service = sheets.get_sheets_api_service()

    spreadsheet_id = sheets.get_spreadsheet_id_from_url(url)
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id, includeGridData=True).execute()

    arkhamset = read_set_info_sheet(spreadsheet['sheets'][0])
    arkhamset['cards'] = read_cards_sheet(spreadsheet['sheets'][1])
    if get_scenarios:
        arkhamset['scenarios'] = read_scenarios_sheet(spreadsheet['sheets'][2])
    else:
        arkhamset['scenarios'] = []

    return arkhamset
"""
