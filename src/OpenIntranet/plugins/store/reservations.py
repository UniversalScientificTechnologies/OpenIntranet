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
		self.render('store/reservations/home.hbs')



	def post(self):

		group = self.get_argument("group", "components")

		if group=='components':
			reservations_groups = list(self.mdb.stock_operation.aggregate([
					{"$match": {'type': 'reservation'}},
					{"$lookup": {"from": "production", "localField": "origin_id", "foreignField": "_id", "as": "production_info"}},
					{"$lookup": {"from": "stock", "localField": "cid", "foreignField": "_id", "as": "component_info"}},
					{"$sort": {'_id': 1}},
					{"$group": {'_id': '$cid', 'origin': {"$first": "$origin"}, 'reservations': {"$push": "$$ROOT"}}},
				]))

			self.render('store/reservations/reservation_table_components.hbs', reservations_groups=reservations_groups)
		
		elif group=='origin':
			reservations_groups = list(self.mdb.stock_operation.aggregate([
					{"$match": {'type': 'reservation'}},
					{"$lookup": {"from": "production", "localField": "origin_id", "foreignField": "_id", "as": "production_info"}},
					{"$lookup": {"from": "stock", "localField": "cid", "foreignField": "_id", "as": "component_info"}},
					{"$sort": {'_id': 1}},
					{"$group": {'_id': '$origin_id', 'origin': {"$first": "$origin"}, 'reservations': {"$push": "$$ROOT"}}},
				]))

			self.render('store/reservations/reservation_table_origin.hbs', reservations_groups=reservations_groups)
