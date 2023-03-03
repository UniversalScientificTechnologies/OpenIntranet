import json
import pprint
from bson import ObjectId
import bson
import pymongo
from plugins import BaseHandler

ROLE_INVOICE_MODIFY ='invoice-sudo'
ROLE_INVOICE_VIEW = 'invoice-access'

BAD_REQUEST_400 = 400
FORBIDDEN_403 = 403
INTERNAL_SERVER_ERROR_500 = 500

class InvoiceSingleHandler(BaseHandler):
    def get(self, id):
        '''get invoice'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_VIEW in roles_current_user:
            self.send_error(FORBIDDEN_403)

        try:
            invoice = self.mdb.invoice.find_one({'_id': ObjectId(id)})
            self.write(bson.json_util.dumps(invoice))
        except Exception as e:
            print(str(e))
            self.send_error(404)
            

    def put(self, id):
        '''mofify invoice'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_MODIFY in roles_current_user:
            self.send_error(FORBIDDEN_403)

        try:
            updated_invoice = json.loads(self.request.body)
            self.mdb.invoice.update_one({"_id": ObjectId(id)}, {"$set": updated_invoice})
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(updated_invoice))
        except ValueError:
            self.send_error(BAD_REQUEST_400)
        except pymongo.errors.NotFound:
            self.send_error(404)
        except Exception as e:
            print(str(e))
            self.send_error(404)

    def delete(self, id):
        '''delete invoice'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_MODIFY in roles_current_user:
            self.send_error(FORBIDDEN_403)

        try:
            invoice_id = ObjectId(id)
            result = self.mdb.invoice.delete_one({'_id': invoice_id})
            
            if result.deleted_count == 1:
                self.write('Invoice deleted successfully')
            else:
                self.write('Invoice not found')
        except Exception as e:
            print(str(e))
            self.send_error(404)
            

class InvoiceMultipleHandler(BaseHandler):
    def post(self):
        '''new invoice'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_MODIFY in roles_current_user:
            self.send_error(FORBIDDEN_403)

        try:
            new_invoice = json.loads(self.request.body)
            pprint.pprint(new_invoice)
            self.mdb.invoice.insert_one(new_invoice)
            self.write("ok")
        except Exception as e:
            print(str(e))
            self.send_error(404)


    def get(self):
        '''get all invoices'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_VIEW in roles_current_user:
            self.send_error(FORBIDDEN_403)
        try:
            all_invoices = self.mdb.invoice.find({})
            invoices_json = json.dumps(list(all_invoices), cls=MdbEncoder)
            pprint.pprint(invoices_json)
            self.set_header("Content-Type", "application/json")
            self.write(invoices_json)
            self.finish()
        except Exception as e:
            print(str(e))
            self.send_error(404)


    def delete(self):
        '''delete all invoices'''
        roles_current_user = self.get_current_user()["role"]

        if not ROLE_INVOICE_MODIFY in roles_current_user:
            self.send_error(FORBIDDEN_403)

        try:
            result = self.mdb.invoice.delete_many({})
            deleted_count = result.deleted_count
            self.write(f"Deleted {deleted_count} invoices")
        except Exception as e:
            print(str(e))
            self.send_error(INTERNAL_SERVER_ERROR_500)


class MdbEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)