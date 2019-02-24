# Module for reading/writing Arkham Horror LCG set data to/from a Google Sheets
# spreadsheet

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import arkham_data


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

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


def simple_row(*args):
    row = {
        'values': [
            {'userEnteredValue': {"stringValue": x}}
            for x in args
        ]
    }
    return row


def row_from_side(side, number, quantity, encounter_set):
    fields = [
        side.get('name', ''), number, side.get('image_url', ''), 'False',
        quantity, encounter_set
    ]
    fields += [side['data'].get(f, '') for f in arkham_data.side_data_fields]
    return simple_row(*fields)


def rows_from_card(card):
    quantity = card.get('quantity', '')
    encounter_set = card.get('encounter_set', '')

    rows = []
    if arkham_data.is_double_sided(card):
        number_front = str(card['number']) + 'a'
        rows.append(row_from_side(card['front'], number_front, quantity, encounter_set))

        number_back = str(card['number']) + 'b'
        rows.append(row_from_side(card['back'], number_back, quantity, encounter_set))

    else:
        rows.append(row_from_side(card['front'], card['number'], quantity, encounter_set))

    return rows



def create_set_info_sheet(service, arkhamset):
    sheet = {
        'properties': {
            'title': 'Set',
            'index': 0,
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': [
                    simple_row('Name:', arkhamset['name']),
                    simple_row('Campaign:'),
                    simple_row('Campaign Code:'),
                    simple_row('Type:'),
                ],
            },
        ],
    }
    # TODO: guess type of set
    # TODO: bold field names
    return sheet


def create_cards_sheet(service, arkhamset):
    header_fields = ['Name', 'Number', 'Image URL', 'Mini', 'Quantity', 'Encounter Set']
    header_fields += arkham_data.side_data_fields
    rows = [simple_row(*header_fields)]
    for card in arkhamset['cards']:
        rows.extend(rows_from_card(card))

    sheet = {
        'properties': {
            'title': 'Cards',
            'index': 1,
        },
        'data': [
            {
                'startRow': 0,
                'startColumn': 0,
                'rowData': rows
            },
        ],
    }
    # TODO: set formatting and metadata
    #       frozen rows/columns
    #       bold header
    #       color columns not obtainable from cardgamedb

    return sheet


def create_scenarios_sheet(service, arkhamset):
    fields = ['Scenario Number', 'Scenario Name', 'Section', 'Name',
        'Number', 'Source Set ID', 'Quantity']
    header = simple_row(*fields)
    sheet = {
        'properties': {
            'title': 'Scenarios',
            'index': 2,
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
    # TODO: set formatting and metadata
    #       frozen row
    #       bold header
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
                    simple_row('Help info goes here.'),
                ],
            },
        ],
    }
    # TODO: metadata to make this sheet readable (column/row sizes, wrapping, etc)
    return sheet


def create_spreadsheet_for_set(arkhamset):

    service = get_sheets_api_service()

    spreadsheet = {
        'properties': {
            'title': 'Arkham Horror LCG Set Data',
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


def read_set(url):
    # TODO: read set from a spreadsheet
    return None
