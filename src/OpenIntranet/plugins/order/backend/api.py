#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from pydoc import describe
from re import I
from typing import Dict, List
from urllib import response

import bson.json_util
from bson.objectid import ObjectId
from pytz import AmbiguousTimeError
import tornado
import tornado.options
from bson import ObjectId, is_valid
from dateutil.relativedelta import relativedelta
from tornado.web import HTTPError

from plugins import BaseHandler, order, password_hash
from plugins import BaseHandlerOwnCloud
from plugins.helpers import database_user as udb
from plugins.helpers import str_ops
from plugins.helpers.contract_generation import generate_contract
from plugins.helpers.doc_keys import CONTRACT_DOC_KEYS
from plugins.helpers.emails import generate_validation_token, generate_validation_message, send_email
from plugins.helpers.exceptions import BadInputHTTPError, MissingInfoHTTPError, ForbiddenHTTPError
from plugins.helpers.mdoc_ops import find_type_in_addresses, update_workspans_contract_id
from plugins.helpers.owncloud_utils import get_file_url, generate_contracts_directory_path, \
    generate_documents_directory_path
from plugins.order.backend.orders import Order
from plugins.users.backend.helpers.api import ApiJSONEncoder


class GeneralOrderHandler(BaseHandler):
    """handles requests at path ../api/orders"""
    def delete(self):
        pass
        # TODO 
        # delete all orders
        # propper response

    def get(self):
        orders = list(self.mdb.order.find({}))
        if orders is None:
            print("orders are empty")
        self.write(bson.json_util.dumps(orders))


    def post(self):
        """Creates new order"""
        try:
            order = Order(json.loads(self.request.body))
            order_date = order.get("date_of_creation")
            print(type(order_date))
            print(order_date)
            
            self.mdb.order.insert_one(order)
            print("New Order inserted")
        except Exception as e:
            # 400 invalid data in request
            self.send_error(400)
            print("Error:", e)



class SingleOrderHandler(BaseHandler):
    """handles requests at path ../api/orders/<uid>"""
    def delete(self, id):
        try:
            self.mdb.order.delete_one({'_id': ObjectId(id)})
            print('order deleted')
        except Exception as e:
            pass
        # TODO propper responses, auth


    def get(self, id):
        order = self.mdb.order.find_one({'_id': ObjectId(id)})
        if order is None:
            print(f"order with id {id} not found")
            self.send_error(404)
        else:
            try:
                finite_order = Order(order)
                self.write(bson.json_util.dumps(finite_order))
            except Exception as e:
                print("invalid record in database:", str(e))
                self.write(bson.json_util.dumps(order))
                

    def put(self, id):
        try:
            order: Order = Order( json.loads(self.request.body) )
            order.remove_id()
            self.mdb.order.update_one(
                {"_id": ObjectId(id)},
                {'$set': order },
            )
            print("Order PUT completed")
        except Exception as e:
            self.send_error(404)
            print("invalid order:", str(e))