# Module for reading/writing Arkham Horror LCG set data to/from a Google Sheets
# spreadsheet

# TODO: update template with more help info for scenario sheet and link to
# example

# TODO: scenario data object shouldn't contain unique IDs of external cards.
# just store the name of the source.

import re
import uuid
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import arkham_common

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

sheet_template_filename = 'template.pickle'


class SheetDataError(Exception):
    """Base class for exceptions in this module."""
    pass


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


def row_from_side(card, face):
    number = card['number']
    if face == 'front':
        number += 'a'
    elif face == 'back':
        number += 'b'
    else:
        face = 'front'
    row = [ card[face].get('name', ''), number, card['id'], card[face]['image_url'],
            card.get('quantity', ''), card.get('encounter_set', '')]
    row += [card[face]['data'].get(f, '') for f in arkham_common.side_data_fields]
    return row


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

    # TODO: process result to make sure it worked


def fill_cards_sheet(service, spreadsheet_id, arkhamset):
    rows = []
    arkhamset['cards'].sort(key=lambda c: c.get('number', '999'))
    for card in arkhamset['cards']:
        if 'id' not in card or not card['id']:
            card['id'] = str(uuid.uuid4())

        if arkham_common.is_double_sided(card):
            new_rows = [row_from_side(card, 'front'), row_from_side(card, 'back')]
        else:
            new_rows = [row_from_side(card, '')]
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

    # TODO: process result to make sure it worked


def fill_scenario_sheet(service, spreadsheet_id, arkhamset):
    section_names = ['Act', 'Agenda', 'Location', 'Encounter', 'Setup']
    sections = {s: [] for s in section_names}

    for card in arkhamset['cards']:
        type = card['front']['data'].get('Type', '')
        if type in ['Act', 'Agenda', 'Location']:
            sections[type].append(card)
        elif type in ('Treachery', 'Enemy'):
            sections['Encounter'].append(card)
        elif (  type in ('Scenario', 'Story')
                or card['front']['data'].get('Class', '')
                not in ('Guardian', 'Seeker', 'Rogue', 'Mystic', 'Survivor', 'Neutral')):
            sections['Setup'].append(card)

    rows = []
    for s in section_names:
        if sections[s]:
            new_rows = [['', card['id'], card['front']['name'], card['number']] for card in sections[s]]
            new_rows[0][0] = s
            rows.extend(new_rows)

    range = "Scenarios!E2:H{}".format(1 + len(rows))
    value_input_option = 'USER_ENTERED'
    body = {
        'range': range,
        'values': rows,
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption=value_input_option, body=body).execute()

    # TODO: process result to make sure it worked



def create_spreadsheet_for_set(arkhamset):
    if 'id' not in arkhamset:
        arkhamset['id'] = str(uuid.uuid4())

    print('Starting Google Sheets API Service... ', end='')
    service = get_sheets_api_service()
    print('Done.')

    print('Creating template sheet... ', end='')
    with open(sheet_template_filename, 'rb') as sheet_template_file:
        spreadsheet = pickle.load(sheet_template_file)

    spreadsheet['properties']['title'] = 'Arkham Horror LCG: {}'.format(arkhamset['name'])
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
    fill_scenario_sheet(service, spreadsheet_id, arkhamset)
    print('Done.')

    return spreadsheet.get('spreadsheetUrl')


def get_string_from_cell(cell):
    return cell.get('userEnteredValue', {}).get('stringValue', '')


def read_row(row):
    return [get_string_from_cell(cell) for cell in row['values']]


def read_set_info_sheet(sheet):
    rows = sheet['data'][0]['rowData']

    try:
        column = [get_string_from_cell(row['values'][1]) for row in rows]
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
        name, number, id, image_url, quantity, encounter_set, *fields = read_row(row)

        try:
            number, face = arkham_common.get_number_and_face(number)
        except ValueError:
            error_msg = "couldn't read number {}".format(number)
            raise SheetDataError(errormsg)

        side_data = dict(zip(arkham_common.side_data_fields, fields))
        side = {
            'name': name, 'image_url': image_url, 'data': side_data,
        }
        card = {
            'id': id,
            'number': number,
            'quantity': quantity,
            'encounter_set': encounter_set,
        }

        if face:
            if number in incomplete_cards:
                if face in incomplete_cards[number]:
                    error_msg = 'found two sides labeled "{}" for card number {}'.format(face, number)
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
    rows = map(read_row, sheet['data'][0]['rowData'][1:])

    scenario_dict = {}
    last = [''] * 5

    for row in rows:
        try:
            for i in range(5):
                row[i] = row[i] or last[i]
            last = row[:5]

            scenario_name = row[4]
            section = row[5]

            card_fields = dict(zip(
                ['id', 'name', 'card_number', 'quantity', 'source'], row[6:11]
            ))
            if not card_fields['quantity'] and section in ('Act', 'Agenda', 'Location'):
                card_fields['quantity'] = 1
            scenario = dict(zip(
                ['campaign_code', 'campaign_name', 'scenario_number', 'scenario_name', section],
                row[:5] + [[card_fields]]
            ))
        except IndexError:
            raise SheetDataError

        # merge this card into the existing list of scenarios
        if scenario_name not in scenario_dict:
            scenario_dict[scenario_name] = scenario
        elif section not in scenario_dict[scenario_name]:
            scenario_dict[scenario_name][section] = scenario[section]
        else:
            scenario_dict[scenario_name][section].extend(scenario[section])

    scenarios = scenario_dict.values()
    return scenarios


def get_spreadsheet_id_from_url(url):
    m = re.search('/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not m:
        print('{} is not a properly formatted google sheets URL'.format(url))
        return ''
    id = m.group(1)
    return id


def read_set(url):
    service = get_sheets_api_service()

    spreadsheet_id = get_spreadsheet_id_from_url(url)
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id, includeGridData=True).execute()

    arkhamset = read_set_info_sheet(spreadsheet['sheets'][0])
    arkhamset['cards'] = read_cards_sheet(spreadsheet['sheets'][1])
    arkhamset['scenarios'] = read_scenarios_sheet(spreadsheet['sheets'][2])

    return arkhamset


if __name__ == '__main__':
    pass
