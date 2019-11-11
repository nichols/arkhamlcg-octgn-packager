# Module for reading/writing an Arkham Horror LCG set object (as defined in
# arkham_common) to/from a Google Sheets spreadsheet. This provides an easy
# way to enter missing data.

import re
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

sheets_auth_token_filename = 'token.pickle'

_sheets_api_service = None


def get_sheets_api_service():
    global _sheets_api_service
    if _sheets_api_service is None:
        print('Starting Google Sheets API Service... ', end='')
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(sheets_auth_token_filename):
            with open(sheets_auth_token_filename, 'rb') as token:
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
            with open(sheets_auth_token_filename, 'wb') as token:
                pickle.dump(creds, token)
        print('Done.')
        _sheets_api_service = build('sheets', 'v4', credentials=creds)

    return _sheets_api_service


def get_string_from_cell(cell):
    return cell.get('userEnteredValue', {}).get('stringValue', '')


def read_row(row):
    return [get_string_from_cell(cell) for cell in row['values']]


def get_spreadsheet_id_from_url(url):
    m = re.search('/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not m:
        raise ValueError('{} is not a properly formatted google sheets URL'.format(url))
    id = m.group(1)
    return id
