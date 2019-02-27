# Module for reading/writing Arkham Horror LCG set data to/from a Google Sheets
# spreadsheet

import re
import uuid
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import arkham_data

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

hex_colors = {
    'white': '#ffffff',
    'red': '#f4cccc',
    'orange': '#fce5cd',
    'yellow': '#fff2cc',
    'green': '#d9ead3',
    'blue': '#c9daf8',
    'purple': '#d9d2e9',
}


class SheetDataError(Exception):
    """Base class for exceptions in this module."""
    pass


def hex_color_to_sheets_object(hex_color):
    if not re.match('#[0-9a-f]{6}', hex_color):
        raise ValueError
    hex_color = hex_color.lstrip('#')
    r, g, b = map(
        lambda x : x / 255,
        tuple(int(hex_color[i:i+2], 16) for i in (0, 2 ,4))
    )
    sheets_color = {'red': r, 'green': g, 'blue': b}
    return sheets_color


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


def make_row(*args, bold=False, bg_color=None):
    bg_color = bg_color or hex_color_to_sheets_object(hex_colors['white'])
    row = {
        'values': [
            {
                'userEnteredValue': {"stringValue": x},
                'userEnteredFormat': {
                    'textFormat': {'bold': bold},
                    'backgroundColor': bg_color,
                },
            }
            for x in args
        ]
    }
    return row


def row_from_side(side, number, id, quantity, encounter_set, face=None):
    bg_color = None
    if face == 'front':
        number += 'a'
    elif face == 'back':
        number += 'b'
        bg_color = hex_color_to_sheets_object(hex_colors['red'])

    fields = [
        side.get('name', ''), number, id, side.get('image_url', ''), 'False',
        quantity, encounter_set
    ]
    fields += [side['data'].get(f, '') for f in arkham_data.side_data_fields]
    return make_row(*fields, bg_color=bg_color)


def rows_from_card(card):
    quantity = card.get('quantity', '')
    encounter_set = card.get('encounter_set', '')
    if not card['id']:
        card['id'] = uuid.uuid4()

    rows = []
    if arkham_data.is_double_sided(card):
        rows.append(row_from_side(card['front'], card['number'], card['id'], quantity, encounter_set, face='front'))
        rows.append(row_from_side(card['back'], card['number'], card['id'], quantity, encounter_set, face='back'))
    else:
        rows.append(row_from_side(card['front'], card['number'], card['id'], quantity, encounter_set))

    return rows


def create_set_info_sheet(service, arkhamset):
    set_id_row = {
        'values': [
            {
                'userEnteredValue': {'stringValue': 'Unique ID'},
                'userEnteredFormat': {
                    'textFormat': {'bold': True},
                },
            },
            {
                'userEnteredValue': {"stringValue": arkhamset['id']},
            },
        ],
    }
    set_name_row = {
        'values': [
            {
                'userEnteredValue': {'stringValue': 'Name:'},
                'userEnteredFormat': {
                    'textFormat': {'bold': True},
                },
            },
            {
                'userEnteredValue': {"stringValue": arkhamset['name']},
            },
        ],
    }

    rows = [
        set_name_row,
        make_row('Type:', bold=True),
        make_row('Campaign:', bold=True),
        make_row('Campaign Code:', bold=True),
    ]

    sheet = {
        'properties': {
            'title': 'Set',
            'index': 0,
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': rows,
            },
        ],
    }
    # TODO: auto resize column B
    # TODO: guess type of set
    return sheet


def get_real_card_number(card):
    n = card.get('number', '999')
    if n[-1] in ['a', 'b']:
        n = n[:-1]
    return int(n)


def create_cards_sheet(service, arkhamset):
    header_fields = ['Name', 'Number', 'Unique ID', 'Image URL', 'Mini', 'Quantity', 'Encounter Set']
    header_fields += arkham_data.side_data_fields
    rows = [make_row(*header_fields, bold=True)]

    arkhamset['cards'].sort(key=get_real_card_number)
    for card in arkhamset['cards']:
        if 'id' not in card or not card['id']:
            card['id'] = str(uuid.uuid4())
        rows.extend(rows_from_card(card))

    sheet = {
        'properties': {
            'title': 'Cards',
            'index': 1,
            'gridProperties': {
                'frozenRowCount': 1,
                'frozenColumnCount': 2,
            },
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': rows
            },
        ],
    }
    # TODO: color columns not obtainable from cardgamedb
    # TODO: auto resize column widths (except text and flavortext)

    return sheet


def create_scenarios_sheet(service, arkhamset):
    fields = ['Scenario Number', 'Scenario Name', 'Section', 'Name',
        'Number', 'Source Set ID', 'Quantity']
    header = make_row(*fields, bold=True)
    sheet = {
        'properties': {
            'title': 'Scenarios',
            'index': 2,
            'gridProperties': {
                'frozenRowCount': 1,
            },
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': [
                    header,
                ],
            },
        ],
    }
    # TODO: print sample row?

    return sheet


def create_help_sheet(service):
    sheet = {
        'properties': {
            'title': 'Help',
            'index': 3,
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': [
                    # TODO: print actual help text
                    make_row('Help info goes here.'),
                ],
            },
        ],
    }
    # TODO: metadata to make this sheet readable (column/row sizes, wrapping, etc)
    return sheet


def create_spreadsheet_for_set(arkhamset):
    if 'id' not in arkhamset or not arkhamset['id']:
        arkhamset['id'] = str(uuid.uuid4())

    service = get_sheets_api_service()

    spreadsheet = {
        'properties': {
            'title': 'Arkham Horror LCG: {}'.format(arkhamset['name']),
        },
        'sheets': [
            create_set_info_sheet(service, arkhamset),
            create_cards_sheet(service, arkhamset),
            create_scenarios_sheet(service, arkhamset),
            create_help_sheet(service)
        ],
    }

    spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
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
        name, number, id, image_url, mini, quantity, encounter_set, *fields = read_row(row)

        try:
            m = re.match('^(\d*)([ab]?)$', number)
            number = m.group(1)
            ab = m.group(2)
        except AttributeError:
            print("couldn't read number {}".format(number))
            raise

        if ab == 'a':
            ab = 'front'
        elif ab == 'b':
            ab = 'back'
        elif ab:
            raise SheetDataError

        side_data = {arkham_data.side_data_fields[i]: fields[i] for i in range(len(fields))}
        side = {
            'name': name, 'image_url': image_url, 'data': side_data,
        }
        card = {
            'id': id,
            'mini': mini,
            'number': number,
            'quantity': quantity,
            'encounter_set': encounter_set,
        }

        if ab:
            if number in incomplete_cards:
                if ab in incomplete_cards[number]:
                    raise SheetDataError
                incomplete_cards[number][ab] = side
                cards.append(incomplete_cards[number])
                del incomplete_cards[number]
            else:
                card[ab] = side
                incomplete_cards[number] = card
        else:
            card['front'] = side
            cards.append(card)

    return cards


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
            card_fields = dict(zip(
                ['name', 'card_number', 'id', 'set_id', 'quantity'],
                row[4:]
            ))
            scenario = dict(zip(
                ['campaign', 'scenario_number', 'scenario_name', section],
                row[:3] + [[card_fields]]
            ))
        except IndexError:
            raise SheetDataError

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
