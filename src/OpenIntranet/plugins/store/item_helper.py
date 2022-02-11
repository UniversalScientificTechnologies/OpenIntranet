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



def get_items_last_buy_price(db, item):

    packets = list(db.stock.find({'_id': ObjectId(item)}, {'packets._id': 1}))[0]['packets']
    packets = [x['_id'] for x in packets]

    item_query = [
        {"$match": {"pid": {"$in": packets}}},
        {"$sort": {"_id": -1}},
        {"$match": {"type": "buy"}},
        {"$limit": 1},
        {"$project": {"unit_price": 1}}
    ]

    uprice = list(db.stock_operation.aggregate(item_query))[0]["unit_price"]
    return uprice

