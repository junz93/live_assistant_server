import configparser

import os.path

from pathlib import Path


config_dir = os.path.join(os.path.dirname(__file__), 'conf')

auth_config = configparser.ConfigParser()
auth_config.read(os.path.join(config_dir, 'auth.ini'))

print(auth_config.sections())
