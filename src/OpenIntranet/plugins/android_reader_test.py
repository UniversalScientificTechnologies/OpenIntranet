#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
from . import Intranet
from . import BaseHandler
# from pyoctopart.octopart import Octopart
import json
import bson.json_util
import urllib
import datetime

import collections, urllib, base64, hmac, hashlib, json


def get_plugin_handlers():
    plugin_name = get_plugin_info()["name"]

    return [
        (r'/{}'.format(plugin_name), hand_bi_home),
        (r'/{}/'.format(plugin_name), hand_bi_home),
    ]


def get_plugin_info():
    return {
        "name": "android_barcode",
        "entrypoints": [
            {
                "title": "Android čtečka",
                "url": "/android_barcode",
                "icon": "android",
            }
        ],
        "role": ["sudo"]
    }


class hand_bi_home(BaseHandler):
    def get(self, data=None):
        roles = self.authorized(['andorid'], sudo=True)
        print(">>>>>", roles)

        self.render("android_barcode.home.hbs", title="UST intranet", parent=self)
