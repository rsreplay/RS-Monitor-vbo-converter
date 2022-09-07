import json
import os
import sys

from bundle import bundle_dir, frozen

VERSION_LATEST = 1

if frozen:
    json_path = os.path.dirname(sys.executable) + '/config.json'
else:
    json_path = bundle_dir + 'config.json'

config = None

default_config = {
    'version': VERSION_LATEST,
    'lastDir': '',
    'checkboxes': {
        'exportVbo': True,
        'exportCsv': False,
        'exportRawCsv': False,
        'exportRawXslx': False
    }
}

if not os.path.exists(json_path):
    with open(json_path, 'w') as f:
        f.write(json.dumps(default_config, indent=2))


class RSMConfig:
    _instance = None

    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RSMConfig, cls).__new__(cls)
            # Put any initialization here.
            cls.load(cls._instance)
        return cls._instance

    def __init__(self) -> None:
        pass

    def __getitem__(self, item):
        return self._config[item]

    def __setitem__(self, key, value):
        self._config[key] = value

    def save(self):
        with open(json_path, 'w') as config_file:
            dumps = json.dumps(self._config, indent=2)
            print(dumps)
            config_file.write(dumps)

    def load(self):
        with open(json_path, 'r') as config_file:
            self._config = json.loads(config_file.read())

            try:
                version = self._config['version']
            except KeyError:
                version = 0

        if version < VERSION_LATEST:
            if version < 1:
                self._config = {'version': 1, **self._config}

            # if version < 2:
            #     for p in self._config['probes']:
            #         p['nickname'] = ''
            #     self._config['version'] = 2

            self.save()


config = RSMConfig()
