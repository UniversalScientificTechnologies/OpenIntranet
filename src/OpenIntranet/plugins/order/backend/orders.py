#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from pydoc import describe
from re import I
import this
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
    def __init__(self, val):
        def convert_date(date_to_convert: str, date_format="%Y-%m-%dT%H:%M:%S.%fZ") -> datetime:
            """converts date from string (default js json date format) to datetime.datetime"""
            try:
                converted_data =  datetime.strptime(date_to_convert, date_format)
                return converted_data
            except ValueError:
                raise

        super().__init__(val)
        
        this_date = self.get("date_of_creation")
        if isinstance(this_date, str):
            try:
                self.update({"date_of_creation": convert_date(this_date)})
            except ValueError:
                raise
        self.validate()


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
        self.__validate_key_general("date_of_creation", datetime)
        self.__validate_key_general("customer", dict)
        self.__validate_key_general("items", list)
        self.__validate_key_general("price_total", float)
        self.__validate_key_general("price_to_pay", float)
        
        # TODO validate keys:vals more specificaly (price > 0 etc)
        if self.get("price_total") < 0:
            raise ValueError("invalid price_total: ", self.get("price_total"))
        elif self.get("price_to_pay") < 0:
            raise ValueError("invalid price_to_pay: ", self.get("price_to_pay"))

        # for item in self.get("items"):

       

    def set_id(self, id):
        if isinstance(id, str):
            self.update({'_id': ObjectId(id)})
        elif isinstance(id, ObjectId):
            self.update({'_id': id})
        else:
            raise TypeError('Invalid id type given (str of ObjectId required)')

    
    def remove_id(self):
        """removes _id if any"""
        try:
            self.pop('_id')
        except KeyError:
            pass # Id was not set


    def get_id_as_str(self, default_ret=None):
        """gets id as str, when not found returns default_ret (None is default)"""
        id = self.get('_id')
        if id is not None and (isinstance(id, ObjectId) or isinstance(id, str)):
            return str(id)
        return default_ret


    def __validate_key_general(self, keyname: str, expected_type):
        """keyname in dict and has given type; raise propper exception if not"""
        value = self.get(keyname)
        if value is None:
            raise KeyError(f"key {keyname} not present in order")
        if not isinstance(value, expected_type):
            raise TypeError(f"Order {keyname} is not {str(expected_type)} type. Type given: {str(type(value))}")


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
        record = self.mdb.order.find_one({'_id': ObjectId(id)})
        order: Order

        if record is None:
            # TODO render specific page with error message 
            # or move db.get to frontend (ajax)
            pass
            
        try:
            order = Order(record)
        except Exception as e:
            order = record
            print("invalid record in database:", str(e))

        title = "Upravujete objednávku '{}'".format(order["name"])
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
