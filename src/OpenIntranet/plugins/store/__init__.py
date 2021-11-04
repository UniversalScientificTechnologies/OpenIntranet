from .store import hand_bi_home as home
from .store import get_plugin_handlers as handlers
from .component import get_plugin_handlers as handlers_2
from .popover import get_plugin_handlers as handlers_3

from .. import BaseHandler


plugin_version = 1

def get_plugin_handlers():
    return handlers() + handlers_2() + handlers_3()


def get_plugin_info():
    return {
        "name": "store",
        "entrypoints": [
            {
                "title": "Sklad",
                "url": "/store",
                "icon": "store",
            }
        ],
        "role": ["sudo", "sudo-store", "store-manager", "store-user"]
    }

def plugin_init(db):
    actual_data = db.intranet_plugins.find_one({'_id': 'store'})

    if not actual_data: # Prvni spusteni pluginu... 
        print("Plugin 'store' byl spuštěn poprvé. Pokusím se ho nainstalovat.. ")

        structure = {
            '_id': 'store',
            'version': plugin_version,
            'data': { 'data_import': {}}
        }
        db.intranet_plugins.insert_one(structure)

    else:
        actual_version = actual_data['version']


