#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from pydoc import describe
from re import I
from typing import Dict, List
from attr import validate

import bson.json_util
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

"""
Role:
základní uživatel nemá speciální roli jelikož všichni jsou základními uživateli
users-accountant - Účetní
users-sudo - Admin
"""

ROLE_SUDO = "users-sudo"
ROLE_ACCOUNTANT = "order-view, order-manager"


class Order(dict):
    """Order dict can be converted to Order type for convinient methods"""

    def is_valid(self):
        try:
            self.validate()
            return True
        except:
            return False

    def validate(self, id_incluaded:bool=False, date_included:bool=False):
        """
        Raises exeption when order invalid.
        id_icluded: check presence of id
        Whether correct parameters and data values are valid:
        - name
        - description
        - customer (name, other_info)
        - items: list (for each item)
        - prices (price_total, price_to_pay)
        """
        if id_incluaded:
            self.__validate_key_general("_id", ObjectId)
        self.__validate_key_general("name", str)
        self.__validate_key_general("description", str)
        self.__validate_key_general("customer", dict)
        self.__validate_key_general("items", list)
        self.__validate_key_general("price_total", float)
        self.__validate_key_general("price_to_pay", float)
        
        # TODO validate keys:vals more specificaly (price > 0 etc)
       

    def set_id(self, id):
        if isinstance(id, str):
            self.update({'_id': ObjectId(id)})
        elif isinstance(id, ObjectId):
            self.update({'_id': id})
        else:
            raise TypeError('Invalid id type given (str of ObjectId required)')


    def get_id_as_str(self, default_ret=None):
        """gets id as str, when not found returns default_ret (None is default)"""
        id = self.get('_id')
        if id is not None and (isinstance(id, ObjectId) or isinstance(id, str)):
            return str(id)
        return default_ret


    def __validate_key_general(self, keyname: str, type):
        """keyname in dict and has given type; raise propper exception if not"""
        value = self.get(keyname)
        if value is None:
            raise KeyError(f"key {keyname} not present in order")
        if not isinstance(value, str):
            raise TypeError(f"Order {keyname} is not {str(type)} type")


class NewOrderFormHandler(BaseHandler):
    def get(self):
        title = "Vytváříte novou objednávku"
        self.render(
            "../plugins/order/frontend/orders.view.hbs",
            order=None,
            view_title=title
        )


class ModificationOrderFormHandler(BaseHandler):
    def get(self, id):
        order: Order = Order(
            self.mdb.order.find_one({'_id': ObjectId(id)})
        )
        title = "Upravujete objednávku '{}'".format(order["name"])
        if order is None:
            print("None")
        else:
            print(order)
        self.render(
            "../plugins/order/frontend/orders.view.hbs",
            order=order,
            view_title=title
        )


class HomeHandler(BaseHandler):
    def get(self):
        orders = self.mdb.order.find()
        self.render(
            "../plugins/order/frontend/orders.overview.hbs",
            orders=orders
        )
        # test_simple_order()
