from .backend import orders, api

def get_plugin_handlers():
    order_base_name = "order"

    return [
        #(r'/{}/u/(.*)'.format(order_base_name), users.UserPageHandler),
        (r'/{}'.format(order_base_name), orders.HomeHandler),
        (r'/{}/'.format(order_base_name), orders.HomeHandler),
        (r'/{}/view/new'.format(order_base_name), orders.NewOrderFormHandler),
        (r'/{}/view/([^/]+)?'.format(order_base_name), orders.ModificationOrderFormHandler),
        (r'/{}/api/orders'.format(order_base_name), api.GeneralOrderHandler),
        (r'/{}/api/orders/([^/]+)?'.format(order_base_name), api.SingleOrderHandler),
    ]


def get_plugin_info():
    return {
        "name": "order",
        "entrypoints": [
            {
                "url": "/order",
                "title": "Zakázky",
                "icon": 'bi-file-text',
            },
        ]
    }
