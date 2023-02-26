import json
import pprint
from bson import ObjectId
import bson
from plugins import BaseHandler

ROLE_INVOICE_MODIFY ='invoice-sudo'
ROLE_INVOICE_VIEW = 'invoice-access'

class InvoiceSingleHandler(BaseHandler):
    def get(self, id):
        '''get invoice'''
        try:
            invoice = self.mdb.invoice.find_one({'_id': ObjectId(id)})
            self.write(bson.json_util.dumps(invoice))
        except Exception as e:
            print(str(e))
            self.send_error(404)
            

    def put(self, id):
        '''mofify invoice'''
        # check if valid 
        try:
            new_invoice = json.loads(self.request.body)
            self.mdb.order.insert_one(new_invoice)
        
        # test, complete
        except Exception as e:
            print(str(e))
            # modify code
            self.send_error(404)

    def delete(self, id):
        '''delete invoice'''
        try:
            invoice = list(self.mdb.invoice.delete_one({'_id': ObjectId(id)}))
            self.write(bson.json_util.dumps(invoice))
            self.write("ok")
        except Exception as e:
            print(str(e))
            # modify code
            self.send_error(404)
            

class InvoiceMultipleHandler(BaseHandler):
    # def post(self):
    #     '''new invoice'''
    #     # check if valid 
    #     try:
    #         new_invoice = json.loads(self.request.body)
    #         self.mdb.order.insert_one(new_invoice)
    #         self.write("ok")
    #     except Exception as e:
    #         print(str(e))
    #         self.send_error(404)


    def get(self):
        '''get all invoices'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_VIEW in roles_current_user:
            FORBIDDEN_403 = 403
            self.send_error(FORBIDDEN_403)
        try:
            all_invoices = self.mdb.invoices.find({})
            invoices_json = json.dumps(list(all_invoices))
            self.set_header("Content-Type", "application/json")
            self.write(invoices_json)
            self.finish()
        except Exception as e:
            print(str(e))
            self.send_error(404)
        # return all invoices


    def delete(self):
        '''delete all invoices'''
        # deleet all invoices
        pass

