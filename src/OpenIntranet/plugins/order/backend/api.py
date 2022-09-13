#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from pydoc import describe
from re import I
from typing import Dict, List

import bson.json_util
from bson.objectid import ObjectId
from pytz import AmbiguousTimeError
import tornado
import tornado.options
from bson import ObjectId
from dateutil.relativedelta import relativedelta
from tornado.web import HTTPError

from plugins import BaseHandler, password_hash
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
    def delete(self, id):
        try:
            self.mdb.order.delete_one({'_id': ObjectId(id)})
            print('order deleted')
        except e as Exeption:
            pass
        # TODO propper responses, auth


    def get(self, id):
        try:
            order: Order = Order(
                self.mdb.ordcer.find_one({'_id': ObjectId(id)})
            )
        except e as Exception:
            # TODO proper response
            return
        if order is None:
            # TODO proper response
            return
        order.update({'_id': str(order['_id'])})
        order.update({'date_of_creation': str(order['date_of_creation'])})
        print("got id", order)
        self.write(json.dumps(order))

    def put(self):
        print("putting order")
        print("order:")
        order: Order = Order( json.loads(self.request.body) )
        try:
            order.validate_id()
        except KeyError:
            # TODO order can be putted cause id not found: response
            return
        except TypeError:
            try:
                order.set_id( order.get_id_as_str() )
            except TypeError:
                # TODO order has invalid id: response
                return

        if not order.validate():
            # TODO responce invalid order given
            return
        print(order)
        self.mdb.order.update_one(
            {'_id': order.pop("_id")},
            {'$set': order },
        )


    def post(self):
        try:
            order = Order(json.loads(self.request.body))
            if order.validate():
                self.mdb["order"].insert_one(order)
                print("New Order inserted")
                self.write("Ok")
        except Exception as e:
            print("Error:", e)
            # TODO http response
            return