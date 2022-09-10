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
            order = self.mdb.ordcer.find_one({'_id': ObjectId(id)})
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
        order = json.loads(self.request.body)
        id = order.pop("_id")
        print(order)
        self.mdb.order.update_one(
            {'_id': ObjectId(id)},
            {'$set': order },
        )

    def post(self):
        req_body: dict
        try:
            req_body = json.loads(self.request.body)
        except Exception as e:
            print("Error:", e)
            # TODO http response
            return

        name = req_body["name"]
        description = req_body["description"]
        customer = req_body["customer"]
        customer_name = customer["name"]
        customer_info = customer["other_info"]

        items: list = []
        price_total: float = 0
        try:
            requsted_items = req_body["items"]

            for req_item in requsted_items:
                # TODO check whether each param valid (price > 0, etc)
                item_to_insert = {
                    "name": req_item["name"],
                    "description": req_item["description"],
                    "store_link": req_item["store_link"],
                    "store_id": req_item["store_id"],
                    "price_per_piece": req_item["price_per_piece"],
                    "discount_percents": req_item["discount_percents"],
                    "discount_Kc": req_item["discount_Kc"],
                    "amount": req_item["amount"],
                    "dph": req_item["dph"],
                    "price_no_dph": req_item["price_no_dph"],
                    "price_total": req_item["price_total"],
                }
                items.append(item_to_insert)
                price_total += float(item_to_insert["price_total"])
        except Exception as e:
            print(e)
            # empty order
            # TODO ask if allow empty order..?
            items = []

        new_order = {
            "name": name,
            "description": description,
            "customer": {
                "name": customer_name,
                "other_info": customer_info
            },
            "price_total": price_total,
            "price_to_pay": price_total,
            "date_of_creation": datetime.utcnow(),
            "items": items
        }

        try:
            self.mdb["order"].insert_one(new_order)
            print("New Order inserted")
            self.write("Ok")
        except Exception as e:
            print("Exception when inserting new order:")
            print(e)
