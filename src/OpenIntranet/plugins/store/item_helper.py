#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import bson
import bson.json_util
from bson.json_util import dumps
from bson import *
from bson import ObjectId
import datetime

def get_item(db, item):

    item_query = [{ '$match': {"_id": item}},
                

                ]

    print(item_query)
    return list(db.stock.aggregate(item_query))[0]


