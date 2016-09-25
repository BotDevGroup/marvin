import configparser, os

config_filename = "app.ini"
config = configparser.ConfigParser(allow_no_value=True)
config_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filename)
with open(config_filepath, 'r') as f:
    config.read_file(f)
