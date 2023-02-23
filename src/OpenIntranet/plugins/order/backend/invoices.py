from plugins import BaseHandler

"""
Role:
základní uživatel nemá speciální roli jelikož všichni jsou základními uživateli
users-accountant - Účetní
users-sudo - Admin
"""

ROLE_SUDO = "users-sudo"
ROLE_ACCOUNTANT = "order-view, order-manager"


class InvoiceOverview(BaseHandler):
    def get(self):
        try:
            self.render(
                "../plugins/order/frontend/invoices.overview.hbs",
            )
        except Exception as e:
            print(e)


class InvoiceView(BaseHandler):
    def get(self):
        try:
            print("here")
            self.render(
                "../plugins/order/frontend/invoice.new.hbs",
            )
        except Exception as e:
            print(e)