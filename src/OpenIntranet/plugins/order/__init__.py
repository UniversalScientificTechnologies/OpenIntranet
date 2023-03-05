from .backend import orders, api_invoice, invoices

def get_plugin_handlers():
    order_base_name = "order"
    invoice_endpoint_name = "invoices"

    return [
        # orders:
        (r'/{}'.format(order_base_name), orders.HomeHandler),
        (r'/{}/'.format(order_base_name), orders.HomeHandler),
        (r'/{}/view/([^/]+)?'.format(order_base_name), orders.ViewHandler),
        
        # invoices:
        (r'/{}/{}'.format(order_base_name, invoice_endpoint_name), invoices.InvoiceOverview),
        (r'/{}/{}/'.format(order_base_name, invoice_endpoint_name), invoices.InvoiceOverview),
        (r'/{}/{}/new'.format(order_base_name, invoice_endpoint_name), invoices.InvoiceNew),
        (r'/{}/{}/new/'.format(order_base_name, invoice_endpoint_name), invoices.InvoiceNew),
        (r'/{}/{}/([^/]+)?'.format(order_base_name, invoice_endpoint_name), invoices.InvoiceEdit),
        

        # api invoices
        (r'/{}/api/{}'.format(order_base_name, invoice_endpoint_name), api_invoice.InvoiceMultipleHandler),
        (r'/{}/api/{}/([^/]+)?'.format(order_base_name, invoice_endpoint_name), api_invoice.InvoiceSingleHandler),
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
