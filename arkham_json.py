# Module for reading/writing Arkham Horror LCG set data from/to a .json file

import json


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
