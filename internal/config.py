#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import json

_PATH = os.path.dirname(os.path.realpath(__file__))
_JSON = "data.json"

_DEFAULT_JSON = {
        "config": {
            "pomodoro": {
                "name": "Length of pomodoro timer (in seconds)",
                "value": 1500,
                "type": "time"
            },
            "short": {
                "name": "Length of short break (in seconds)",
                "value": 300,
                "type": "time"
            },
            "long": {
                "name": "Length of long break (in seconds)",
                "value": 1800,
                "type": "time"
            },
            "editor": {
                "name": "The editor to use for writing tasks.",
                "value": "/usr/bin/vim",
                "type": "exe"
            }
        }
    }

def get_internal_path():
    return _PATH

def get_configuration():
    json_name = os.path.join(_PATH, _JSON)
    return _Config(json_name)


class _Config:
    def __init__(self, json_name):
        self.json_name = json_name

    def __enter__(self):
        # Load the json file into memory
        if os.path.exists(self.json_name):
            with open(self.json_name, 'r') as json_file:
                try:
                    self.json = json.load(json_file)
                except json.JSONDecodeError:
                    print('Failed to parse the configuration file, '
                            f'found in "{self.json_name}". Please delete or '
                            'manually fix the file.')
                    exit(1)
        else:
            self.json = _DEFAULT_JSON
        return self.json
    
    def __exit__(self, type, value, traceback):
        # Write the json into disk
        with open(self.json_name, 'w') as json_file:
            json.dump(self.json, json_file)

