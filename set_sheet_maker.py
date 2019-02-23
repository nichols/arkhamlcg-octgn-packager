import cardgamedb_scraper
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

"""
# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'
"""

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


def make_set_info_sheet(service, arkhamset):
    sheet = None
    ## TODO: name, ID, and guessed type
    ## TODO: leave number blank, user can fill it in
    return sheet


def make_cards_sheet(service, cards):
    sheet = None
    ## TODO: print header with all the columns
    for card in cards:
        row = card_to_row(card)
        # add row to sheet

    ## TODO: set metadata
    ##      frozen rows/columns
    ##      color columns not obtainable from cardgamedb
    ##
    return sheet


def make_scenarios_sheet(service):
    sheet = None
    ## TODO: print header with all the columns
    ## TODO: set metadata
    ##      frozen row
    return sheet


def make_help_sheet(service):
    sheet = None
    ## TODO: print help messages
    return sheet


def make_spreadsheet_for_set(service, arkhamset):
    """
    spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                        fields='spreadsheetId').execute()
    """
    sheets = [
        make_set_info_sheet(service),
        #make_cards_sheet(service),
        #make_scenarios_sheet(service),
        #make_help_sheet(service)
    ]
    
    spreadsheet = service.spreadsheets(title=title, sheets=sheets)
    ## TODO: set spreadsheet metadata including title


    ## TODO: call create

    return spreadsheet


def make_spreadsheet_for_url(url):
    service = get_sheets_api_service()
    arkhamset = cardgamedb_scraper.get_set(url)
    return make_spreadsheet_for_set(service, arkhamset)


def main():
    if len(sys.argv) < 2:
        print("get-set-data <cardgamedb_url>")
        return
    url = sys.argv[1]
    spreadsheet = make_spreadsheet_for_url()
    print('Spreadsheet ID: {0}'.format(spreadsheet.get('spreadsheetId')))
    ## TODO: print URL?


if __name__ == '__main__':
    main()
