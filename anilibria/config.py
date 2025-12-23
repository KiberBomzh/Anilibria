import tomllib
from pathlib import Path
from os import getenv


HOME = getenv('HOME') + '/.config'
config_home = getenv('XDG_CONFIG_HOME', HOME)

config_path = 'Anilibria/config.toml'
config_file = Path(config_home) / config_path

if config_file.exists():
    try:
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)
    except Exception as err:
        print('Ошибка в конфиге:')
        print(err)
        config = []
else:
    config = []