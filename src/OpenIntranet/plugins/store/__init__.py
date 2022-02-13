from .store import hand_bi_home as home
from .store import get_plugin_handlers as handlers
from .component import get_plugin_handlers as handlers_2
from .popover import get_plugin_handlers as handlers_3
from .reservations import get_plugin_handlers as handlers_4

from .. import BaseHandler


plugin_version = 2

def get_plugin_handlers():
    return handlers() + handlers_2() + handlers_3() + handlers_4()


def get_plugin_info():
    return{
        "role": ['store-access', 'store-sudo', 'sudo', 'store-manager'],
        "name": "store",
        "entrypoints": [
            {
                "title": "Sklad",
                "url": "/store",
                "icon": "bi-shop",
            },
            {
                "title": "Nákup",
                "url": "/store/orders",
                "icon": "bi-cart4",
            },
            {
                "title": "Rezervace",
                "url": "/store/reservations",
                "icon": "bi-journal-bookmark",
            }
        ]
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

        if actual_version == 1:
            for x in list(db.stock.find()):
                #print(x)
                for i, p in enumerate(x.get('packets', [])):
                    i += 1
                    print(i, p)
                    db.stock.update_one({'_id': x['_id'], 'packets._id': p['_id']}, {"$set": {"packets.$.name": "S{:03}".format(i) }})




        # nastav aktualni vezi do DB
        actual_data = db.intranet_plugins.update_one({'_id': 'store'}, {'$set': {'version': plugin_version}})


