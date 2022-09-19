#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
from .. import Intranet
from .. import BaseHandler
from .item_helper import get_component_counts, add_component_to_orderlist
import json
import bson
from bson import ObjectId

from .orders_helper import *

def get_plugin_handlers():
        plugin_name = 'store'

        return [
                (r'/{}/orders'.format(plugin_name), orders_home),
                (r'/{}/order/(.*)/parameters/save'.format(plugin_name), order_parameters_save),
                (r'/{}/order/(.*)/update_from_api'.format(plugin_name), order_update_from_api),
                (r'/{}/order/(.*)'.format(plugin_name), order_edit),
                (r'/{}/orders/orderlist'.format(plugin_name), orders_get_orderlist),
                (r'/{}/orders/order_row'.format(plugin_name), orders_order_row),
                (r'/{}/orders/order_row/select_supplier'.format(plugin_name), orders_order_setsupplier),
                (r'/{}/orders/add_to_orderlist'.format(plugin_name), orders_add_to_orderlist),
        ]


class orders_home(BaseHandler):
    def get(self):
        self.render("store/orders/orders.home.hbs")

class orders_get_orderlist(BaseHandler):
    def get(self):

        wait_list = list(self.mdb.stock_operation.aggregate([
            {"$match": {"type": "order"}},
            {"$sort": {"cid": 1}},
            {"$lookup": {"from": "stock", "localField": "cid", "foreignField": "_id", "as": "component_info"}},
            {"$group": {'_id': "$supplier", "order_rows": {"$push": "$$ROOT"}}},
            {"$sort": {"_id": 1}}
        ]))


        order_list = list(self.mdb.orders.aggregate([

        ]))


        self.render("store/orders/orders.orderlist.hbs", order_list=order_list, wait_list=wait_list,
            OrderStatusText=OrderStatusText)


class order_edit(BaseHandler):
    def get(self, order_id):
        if order_id == 'new':
            order_id = create_empty_order(self.mdb)
            self.redirect('/store/order/{}'.format(order_id))

        order_id = bson.ObjectId(order_id)
        if order_id:
            self.write("OK..."+str(order_id))
            order_details = self.mdb.orders.aggregate([
                {"$match": {'_id': order_id}},
            ])
            self.render('store/orders/order.edit.hbs', order = list(order_details)[0])

class order_parameters_save(BaseHandler):
    def post(self, order_id):
        order_id = bson.ObjectId(order_id)

        supplier = self.get_argument('order_supplier', None)
        identificator = self.get_argument('order_identificator', None)

        self.mdb.orders.update_one({'_id': order_id}, {"$set":{'order_supplier': supplier, 'order_identificator': identificator}})
        self.write("ok")

class orders_order_row(BaseHandler):
    def get(self):
        order_row = ObjectId(self.get_argument('order_row'))

        row = list(self.mdb.stock_operation.aggregate([
            {"$match": {"_id": order_row}},
            {"$lookup": {"from": "stock", "localField": "cid", "foreignField": "_id", "as": "component_info"}},
        ]))

        self.render("store/orders/orders.componet_view.hbs", row=row[0])


class orders_order_setsupplier(BaseHandler):
    def post(self):
        order_row = ObjectId(self.get_argument('order_row'))
        supplier_i = int(self.get_argument('supplier'))

        row = list(self.mdb.stock_operation.aggregate([
            {"$match": {"_id": order_row}},
            {"$lookup": {"from": "stock", "localField": "cid", "foreignField": "_id", "as": "component_info"}},
            {"$project": {"_id":1, "component_info.supplier":1, "cid": 1}}
        ]))[0]
        supplier = row['component_info'][0]['supplier'][supplier_i]
        out = self.mdb.stock_operation.update_one({'_id': row['_id']}, {"$set": {"supplier_id": supplier_i, "supplier": supplier['supplier'], "supplier_symbol": supplier['symbol'] }})

        self.write(str(out))





class order_update_from_api(BaseHandler):
    def get(self, order_id):
        order_id = bson.ObjectId(order_id)
        api_data = order_update_data_from_api(self.mdb, order_id)
        #api_data = json.loads(api_data)

        ## TODO check if currency is CZK (or preset currency)

        for i, item in enumerate(api_data.get('OrderLines', [])):
            print(i, item)

            row_data = {
                'order_id': order_id,
                'supplier_symbol': item.get('MouserPartNumber', None),
                'manufacturer_symbol': item.get('MfrPartNumber', None),
                'count': item.get('Quantity', None),
                'unit_price': item.get('UnitPrice', None),
                'api': True
            }

            self.mdb.orders_items.insert_one(row_data)

        self.write("OK")


class orders_add_to_orderlist(BaseHandler):
    def post(self):

        cid = ObjectId(self.get_argument('cid'))
        count = float(self.get_argument('count', 0))
        origin = self.get_argument('origin', None)
        description = self.get_argument('description', None)

        add_component_to_orderlist(self.mdb, self.logged, count=count, cid=cid, description=description, warehouse=self.get_warehouse()['_id'], origin=origin)

        self.write("OK")
