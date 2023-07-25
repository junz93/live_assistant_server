import configparser
import os.path

from pathlib import Path

# config_dir = Path(__file__).parent.joinpath('conf')
# config_dir = os.path.join(os.path.dirname(__file__), 'conf')
config_dir = './conf'

auth_config = configparser.ConfigParser()
auth_config.read(os.path.join(config_dir, 'auth.ini'), encoding='utf-8')

db_config = configparser.ConfigParser()
db_config.read(os.path.join(config_dir, 'db.ini'), encoding='utf-8')
