#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import bson
import bson.json_util
from bson.json_util import dumps
from bson import *
from bson import ObjectId
import datetime
from .. import BaseHandler
import redis
import collections, urllib, base64, hmac, hashlib, json
from urllib import request, parse


def api_call(action, params, token, app_secret, show_header=False):
    api_url = 'https://api.tme.eu/' + action + '.json';
    params['Token'] = token;

    params = collections.OrderedDict(sorted(params.items()));

    encoded_params = urllib.parse.urlencode(params, '')
    signature_base = 'POST' + '&' + urllib.parse.quote(api_url, '') + '&' + urllib.parse.quote(encoded_params, '')

    hm = hmac.new(bytes(app_secret, encoding='utf8'), signature_base.encode('utf-8'), hashlib.sha1).digest()
    print(hm)
    api_signature = base64.encodestring(hm).rstrip();
    params['ApiSignature'] = api_signature;

    opts = {
        'http': {
            'method' : 'POST',
            'header' : 'Content-type: application/x-www-form-urlencoded',
            'content' : urllib.parse.urlencode(params)
        }
    };

    http_header = {
        "Content-type": "application/x-www-form-urlencoded",
    };

    # create your HTTP request
    print(params)
    req = urllib.request.Request(api_url, bytes(urllib.parse.urlencode(params), encoding='utf8'), http_header);

    # submit your request
    res = urllib.request.urlopen(req);
    html = res.read();

    return json.loads(html);


class tme(BaseHandler):
	#role_module = ['store-sudo', 'store-access', 'store-manager', 'store_read']

	def get(self, component_id = None):
		r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)


		if component_id:
			component_id = bson.ObjectId(component_id)

		sesid = self.get_argument('sesid', None)

		if not sesid and component_id:
			sessid = str(bson.ObjectId())
			session = {
				'source': 'tme',
				'component': str(component_id),
				'symbol': self.get_argument('symbol', ''),
			}
			r.hmset(sessid, session)
			self.redirect('/store/data_import?sesid='+ sessid)

		else:
			session = r.hgetall(sesid)
			print("Moje session")
			print(session)

			data_import_info = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']

			params = {
				'SymbolList[0]': session['symbol'],
				'Country' : 'CZ',
				'Language': 'cs',
				'Currency': 'CZK'
			}
			print(params)

			product_files = api_call('Products/GetProductsFiles', params, data_import_info['tme_user_token'], data_import_info['tme_app_secret'], True);
			parameters = api_call('Products/GetParameters', params, data_import_info['tme_user_token'], data_import_info['tme_app_secret'], True);

			self.write({'files': product_files['Data'], 'parameters': parameters['Data']})

	def tme_get_docs(self):

		#token = '<TOKEN>'
		#app_secret = ''

		params = {
			'SymbolList[0]': 'RPI-PICO',
			'Country' : 'CZ',
			'Language': 'cs',
			'Currency': 'CZK',
		}

		response = api_call('Products/GetPrices', params, token, app_secret, True);
		response = json.loads(response);
		print(response)


		self.write("")

class tme_get_nonce(BaseHandler):

	def get(self):

		tme_token = self.get_argument('token', None)
		tme_app_secret = self.get_argument('app_secret', None)
		tme_user_pin = self.get_argument('user_pin', None)

		if tme_token and tme_app_secret:
			self.mdb.intranet_plugins.update_one({'_id': 'store'}, {"$set": {'data.data_import.tme_token': tme_token, 'data.data_import.tme_app_secret': tme_app_secret}})
			self.write("TME token a TME Secret_key byly uloženy. Nyní je bude Intranet užívat. Nonce kód získáte na <a href='/store/data_import/tme/registr'>této adrese</a>. Více informací se dočtete v oficiální příručce")
			self.finish()
			return 1

		elif not tme_user_pin:


			data_import_info = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']

			response = api_call('Auth/GetNonce', {}, data_import_info['tme_token'], data_import_info['tme_app_secret'], True);
			response = response
			print(response)
			self.mdb.intranet_plugins.update_one({'_id': 'store'}, {"$set": {'data.data_import.tme_user_nonce': response['Data']['Nonce']}})

			self.write(response)
			self.finish()

			return 1

		elif tme_user_pin:
			#self.mdb.intranet_plugins.update_one({'_id': 'store'}, {"$set": {'data.data_import.tme_user_pin': tme_user_pin}})
			data_import_info = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']
			print(data_import_info)

			params = {
				'Token': data_import_info['tme_token'],
				'TempToken': tme_user_pin,
				'Nonce': data_import_info['tme_user_nonce']
			}
			print(params)

			response = api_call('Auth/Init', params, data_import_info['tme_token'], data_import_info['tme_app_secret'], True);
			response = response	
			self.mdb.intranet_plugins.update_one({'_id': 'store'}, {"$set": {'data.data_import.tme_user_token': response['Data']['Token']}})

			self.write("Přistupový kód byl získán... Nyní by přístup do databáze TME měl fungovat. ")
			self.finish()
			return 1

		self.write(response)


class tme_get_status(BaseHandler):

	def get(self):

		try:
			tme_db_status = self.mdb.intranet_plugins.find_one({"_id": "store"})

			tme_db_status = tme_db_status['data'].get("data_import", None)
			if not tme_db_status:
				self.write("TME importer není nastaven. ")
			else:
				self.write("TME importer je nastaven! :) ")

		except:
			self.write("TME importer naní správně nastaven. Zkuste ho nastavit znovu. ")
