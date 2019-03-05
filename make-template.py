#!/usr/bin/env python3

import sys
import pickle
from arkham_sheets import get_sheets_api_service

template_id = '1Mjx2SnlevtwB8_x9g5-Rfwe1NSBKBEjf5Wo5D91WpeE'


def main():
    if len(sys.argv) < 2:
        raise ValueError("Command line argument needed: destination path for template file.")
    template_filename = sys.argv[1]

    service = get_sheets_api_service()
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=template_id, includeGridData=True).execute()
    del spreadsheet['spreadsheetId']
    
    with open(template_filename, 'wb') as template_file:
        pickle.dump(spreadsheet, template_file)
    print("Wrote template file data to {}".format(template_filename))


if __name__ == '__main__':
    main()
