# Module for reading/writing Arkham Horror LCG set data to/from a Google Sheets
# spreadsheet

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
        number += b
    row = [ card[face].get('name', ''), number, card['id'], card[face]['image_url'],
            card.get('quantity', ''), card.get('encounter_set', '')]
    row += [card[face]['data'].get(f, '') for f in arkham_data.side_data_fields]
    return row


def fill_set_info_sheet(service, spreadsheet_id, arkhamset):
    range = 'Set!B2:B6'
    value_input_option = 'USER_ENTERED'
    column = [arkhamset['id'], arkhamset['name'], '', '', '']
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
            rows.extend([   row_from_side(card, 'front'),
                            row_from_side(card, 'back')     ])
        else:
            rows.append(row_from_side(card, ''))

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


def create_spreadsheet_for_set(arkhamset):
    if 'id' not in arkhamset:
        arkhamset['id'] =uuid.uuid4()

    service = get_sheets_api_service()

    with open(sheet_template_filename, 'rb') as sheet_template_file:
        spreadsheet = pickle.load(sheet_template_file)

    spreadsheet['properties']['title'] = 'Arkham Horror LCG: {}'.format(arkhamset['name'])
    spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')

    fill_set_info_sheet(service, spreadsheet_id, arkhamset)
    fill_cards_sheet(service, spreadsheet_id, arkhamset)

    return spreadsheet.get('spreadsheetUrl')


def get_string_from_cell(cell):
    if 'userEnteredValue' not in cell or 'stringValue' not in cell['userEnteredValue']:
        return ''
    else:
        return cell['userEnteredValue']['stringValue']


def read_row(row):
    return [get_string_from_cell(cell) for cell in row['values']]


def read_set_info_sheet(sheet):
    rows = sheet['data'][0]['rowData']

    try:
        column = [get_string_from_cell(row['values'][1]) for row in rows]

        arkhamset = {
            'id': column[0],
            'name': column[1],
            'type': column[2],
            'campaign': column[3],
            'campaign_code': column[4],
        }
    except IndexError:
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

        side_data = dict(zip(arkham_data.side_data_fields, fields))
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


# look up the unique ID of a card from an external set based on its name or number
# TODO:
def lookup_card_id_external(set_id, card_name, card_number):
    return ''


# look up the unique ID of a card in this set based on its number
# TODO:
def lookup_card_id_internal(arkhamset, card_name, card_number):
    return ''



def read_scenarios_sheet(sheet):
    rows = map(read_row, sheet['data'][0]['rowData'][1:])

    scenario_dict = {}
    last = [''] * 3

    for row in rows:
        try:
            for i in range(3):
                row[i] = row[i] or last[i]
            last = row[:3]

            scenario_name = row[2]
            section = row[3]
            card_name, card_number, card_id, set_id, quantity = row[4:9]
        except IndexError:
            raise SheetDataError

        quantity = quantity or 1
        if not set_id:
            card_id = lookup_card_id_internal(arkhamset, card_name, card_number)
        elif not card_id:
            card_id = lookup_card_id_external(set_id, card_name, card_number)

        card_fields = dict(zip(
            ['name', 'card_number', 'id', 'set_id', 'quantity'],
            [card_name, card_number, card_id, set_id, quantity]
        ))
        scenario = dict(zip(
            ['campaign', 'scenario_number', 'scenario_name', section],
            row[:3] + [[card_fields]]
        ))

        # merge this card into the existing list of scenarios
        if scenario_name not in scenario_dict:
            scenario_dict[scenario_name] = scenario
        elif section not in scenarios[scenario_name]:
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
