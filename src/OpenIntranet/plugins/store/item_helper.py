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


def create_reservation(db, user, warehouse=None, cid=None, pid=None, reservated_count=1, description="", origin=None, origin_id=None, flag=[]):
        values = {
            'pid': ObjectId(pid),
            'cid': ObjectId(cid),
            'count': float(0),
            'reserved': reservated_count,
            'cart': 0,
            'unit_price': float(0),
            'type': "reservation",
            'date': datetime.datetime.now(),
            'user': user,
            #'invoice': None,
            #'supplier': None,
            'description': description,
            "flag": flag,
            "origin": origin,
            "origin_id": ObjectId(origin_id),
            "state": 1
        }

        if warehouse:
            values['warehouse'] = warehouse
            
        out = db.stock_operation.insert_one(values)
        return out


def get_reservation_components(db, origin_id=None):

    data = db.stock_operation.aggregate([
            {"$match": {'type': 'reservation', 'origin_id': origin_id}},
            {"$sort": {'_id': 1}},
        ])

    return list(data)