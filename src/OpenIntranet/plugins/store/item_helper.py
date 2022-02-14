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

    uprice = list(db.stock_operation.aggregate(item_query))
    if(len(uprice)):
        return uprice[0]["unit_price"]
    else:
        return 0


def get_component_counts(db, cid, warehouse = None):
    output = {}
    if warehouse:
        current_warehouse_query = [{ '$match': {"_id": cid}},
                    { "$project": {"packets": 1}},
                    { "$unwind": '$packets'},
                    { "$replaceRoot": {"newRoot": {"$mergeObjects":  ["$packets", {"cid": "$_id"}]}}},
                    { "$lookup": { "from": 'store_positions', "localField":'position', "foreignField": '_id', "as": 'position'}},
                    { "$match": { "position": {"$not":{"$size":0}, "$elemMatch":{"warehouse": warehouse}}}},
                    { "$lookup": { "from": 'stock_operation', "localField":'_id', "foreignField": 'pid', "as": 'operations'}},
                    { "$addFields": {
                            "packet_count":  {"$sum": "$operations.count"},
                            "packet_reserv":  {"$sum": "$operations.reserved"},
                            "packet_ordered":  {"$sum": "$operations.ordered"},
                            "packet_price": {
                            "$function":
                                {
                                    "body": '''function(prices, counts) {
                                     let total_counts = Array.sum(counts);
                                     var tmp_count = total_counts;
                                     var total_price = 0;

                                     var c = counts.reverse();
                                     var p = prices.reverse();

                                     for(i in c){
                                         if(c[i] > 0){
                                             if(c[i] < tmp_count){
                                                 total_price += (c[i]*p[i]);
                                                 tmp_count -= c[i]
                                              }
                                              else{
                                                 total_price += (tmp_count*p[i]);
                                                 tmp_count = 0;
                                              }
                                          }

                                      }
                                      return total_price;
                                    }''',
                                    "args": ["$operations.unit_price", "$operations.count"], "lang": "js"
                                }
                            }
                        }
                    },
                    { "$group": {
                            '_id': 'null',
                            'count': {"$sum": '$packet_count'},
                            'price': {"$sum": '$packet_price'},
                            'reserv': {"$sum": '$packet_reserv'},
                            'ordered': {"$sum": '$packet_ordered'},
                        }
                     }
                     ]

        output['current_warehouse'] = list(db.stock.aggregate(current_warehouse_query))
        if(len(output['current_warehouse'])):
            output['current_warehouse'] = output['current_warehouse'][0]
        if(output['current_warehouse'] == []): output['current_warehouse'] = [{}]

    other_warehouse_query = [{ '$match': {"_id": cid}},
                { "$project": {"packets": 1}},
                { "$unwind": '$packets'},
                { "$replaceRoot": {"newRoot": {"$mergeObjects":  ["$packets", {"cid": "$_id"}]}}},
                { "$lookup": { "from": 'store_positions', "localField":'position', "foreignField": '_id', "as": 'position'}},
                { "$lookup": { "from": 'stock_operation', "localField":'_id', "foreignField": 'pid', "as": 'operations'}},
                { "$addFields": {
                        "packet_count":  {"$sum": "$operations.count"},
                        "packet_reserv":  {"$sum": "$operations.reserved"},
                        "packet_ordered":  {"$sum": "$operations.ordered"},
                        "packet_price": {
                        "$function":
                            {
                                "body": '''function(prices, counts) {
                                 let total_counts = Array.sum(counts);
                                 var tmp_count = total_counts;
                                 var total_price = 0;

                                 var c = counts.reverse();
                                 var p = prices.reverse();

                                 for(i in c){
                                     if(c[i] > 0){
                                         if(c[i] < tmp_count){
                                             total_price += (c[i]*p[i]);
                                             tmp_count -= c[i]
                                          }
                                          else{
                                             total_price += (tmp_count*p[i]);
                                             tmp_count = 0;
                                          }
                                      }

                                  }
                                  return total_price;
                                }''',
                                "args": ["$operations.unit_price", "$operations.count"], "lang": "js"
                            }
                        }
                    }
                },
                { "$group": {
                        '_id': 'null',
                        'count': {"$sum": '$packet_count'},
                        'price': {"$sum": '$packet_price'},
                        'reserv': {"$sum": '$operations_cid.reserved'},
                        'creserv': {"$first": '$component_reserv'},
                        'ordered': {"$sum": '$packet_ordered'},
                    }
                 }]

    output['other_warehouse'] = list(db.stock.aggregate(other_warehouse_query))
    if(len(output['other_warehouse'])):
        output['other_warehouse'] = output['other_warehouse'][0]
    if(output['other_warehouse'] == []): output['other_warehouse'] = [{}]

    return output


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

def earse_reservations(db, origin_id):
    db.stock_operation.delete_many({'origin_id': origin_id})


def get_reservation_components(db, origin_id=None):
    data = db.stock_operation.aggregate([
            {"$match": {'type': 'reservation', 'origin_id': origin_id}},
            {"$sort": {'_id': 1}},
        ])

    return list(data)


def add_component_to_orderlist(db, user, cid, count, warehouse=None, description=None, origin=None, origin_id=None):

        values = {
            'pid': None,
            'cid': ObjectId(cid),
            'count': float(count),
            'cart': 0,
            'predicted_unit_price': float(0),
            'unit_price': float(0),
            'type': "order",
            'date': datetime.datetime.now(),
            'user': user,
            'order_id': None,
            'invoice': None,
            'supplier': None,
            'supplier_symbol': None,
            'description': description,
            "origin": origin,
            "origin_id": origin_id,
            "state": 0
        }

        if warehouse:
            values['warehouse'] = warehouse
        if origin_id:
            values['origin_id'] = bson.ObjectId(origin_id)

        out = db.stock_operation.insert_one(values)
        return out