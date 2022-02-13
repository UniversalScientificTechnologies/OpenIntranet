#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
from .. import Intranet
from .. import BaseHandler
import json
import bson
from bson import ObjectId



def get_plugin_handlers():
        plugin_name = 'store'

        return [
                (r'/{}/reservations'.format(plugin_name), reservations_home),

        ]



class reservations_home(BaseHandler):
	def get(self):
		self.write("OK")