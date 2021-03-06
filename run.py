from flask_migrate import Migrate
from os import environ
from sys import exit

from config import config_dict
from app import create_app

get_config_mode = 'Debug'

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid CONFIG_MODE environment variable entry.')

app = create_app(config_mode)

if __name__ == "__main__":
    app.run()
