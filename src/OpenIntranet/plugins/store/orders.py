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

def get_plugin_handlers():
        plugin_name = 'store'

        return [
                (r'/{}/orders'.format(plugin_name), orders_home),
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

		self.render("store/orders/orders.orderlist.hbs", wait_list=wait_list)


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


class orders_add_to_orderlist(BaseHandler):
	def post(self):

		cid = ObjectId(self.get_argument('cid'))
		count = float(self.get_argument('count', 0))
		origin = self.get_argument('origin', None)
		description = self.get_argument('description', None)

		add_component_to_orderlist(self.mdb, self.logged, count=count, cid=cid, description=description, warehouse=self.get_warehouse()['_id'], origin=origin)

		self.write("OK")
