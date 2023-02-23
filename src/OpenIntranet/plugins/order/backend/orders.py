#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from pydoc import describe
from re import I
import this
from typing import Dict, List
#from attr import validate

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


class ViewHandler(BaseHandler):
    def get(self, id):
        print("loading testing view")
        self.render(
            "../plugins/order/frontend/orders.view.hbs"
        )


class HomeHandler(BaseHandler):
    def get(self):
        try:
            self.render(
                "../plugins/order/frontend/orders.overview.hbs",
            )
        except Exception as e:
            print(e)
