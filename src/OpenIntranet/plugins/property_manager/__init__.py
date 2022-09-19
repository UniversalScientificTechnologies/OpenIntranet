from .backend.property_manager import *
#from .. import BaseHandler


def get_plugin_handlers():
    plugin_name = get_plugin_info()["name"]

    return [
        (r'/{}'.format(plugin_name), HomeHandler),
        (r'/{}/'.format(plugin_name), HomeHandler),
    ]


def get_plugin_info():
    return {
        "name": "property_manager",
        "entrypoints": [
            {
                "title": "Property manager",
                "url": "/property_manager",
                "icon": "bi-pc-display",
            }
        ]
    }
