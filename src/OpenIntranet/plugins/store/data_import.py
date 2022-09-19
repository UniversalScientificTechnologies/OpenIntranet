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


def mouser_api_call(action, mouser_key, body = {}, method = "POST", debug = True):
	api_url = "https://api.mouser.com/api/v1/" + action + "?apiKey=" + mouser_key
	print("Mouser api call", api_url)
	print(body)
	response = request.Request(url=api_url, data=bytes(json.dumps(body), encoding='utf8'), headers={'Content-Type': 'application/json'}, method=method	)
	response = json.loads(request.urlopen(response).read())
	print(response)
	return response



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
			products = api_call('Products/GetProducts', params, data_import_info['tme_user_token'], data_import_info['tme_app_secret'], True);

			product_files = product_files['Data']['ProductList'][0]
			parameters = parameters['Data']['ProductList'][0]
			products = products['Data']['ProductList'][0]

			# self.write({'files': product_files['Data'], 'parameters': parameters['Data'], 'products': products})
			self.render('store/store.api.importer.tme.data.hbs', parameters = parameters, products = products, files = product_files)

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



class mouser_data_importer(BaseHandler):
	def get(self, component_id = None):

		if self.get_argument('symbol', None):	
			key = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']['mouser_api_key']			
			r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

			if component_id:
				component_id = bson.ObjectId(component_id)

			sesid = self.get_argument('sesid', None)

			if not sesid and component_id:
				sessid = str(bson.ObjectId())
				session = {
					'source': 'mouser',
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

				body = {
				  "SearchByPartRequest": {
				    "mouserPartNumber": session['symbol']
				  }
				}

				product = mouser_api_call('search/partnumber', key, body)['SearchResults']['Parts'][0]

				# self.write({'files': product_files['Data'], 'parameters': parameters['Data'], 'products': products})
				self.render('store/store.api.importer.mouser.data.hbs',product=product)

		else:
			if self.get_argument('mouser_api_key', None):
				key = self.get_argument('mouser_api_key')
				self.mdb.intranet_plugins.update_one({'_id': 'store'}, {"$set": {'data.data_import.mouser_api_key': key}})
				self.write("New mouser api key was set")

			else:
				# check if mouser is registred
				data_import = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']
				if 'mouser_api_key' in data_import:
					self.write("Mouser api key is set")
				else:
					self.write("Mouser api key is not entered")





class return_data(BaseHandler):
	#role_module = ['store-sudo', 'store-access', 'store-manager', 'store_read']

	def get(self):
		r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)


		sesid = self.get_argument('sesid', None)

		if sesid:
			session = r.hgetall(sesid)
			print("Moje session")
			print(session)

			if session.get('source', '') == 'tme':

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
				products = api_call('Products/GetProducts', params, data_import_info['tme_user_token'], data_import_info['tme_app_secret'], True);

				product_files = product_files['Data']['ProductList'][0]
				parameters = parameters['Data']['ProductList'][0]
				products = products['Data']['ProductList'][0]

				# self.write({'files': product_files['Data'], 'parameters': parameters['Data'], 'products': products})
				self.render('store/store.api.importer.tme.data.hbs', parameters = parameters, products = products, files = product_files)

		if session.get('source', '') == 'mouser':

			key = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']['mouser_api_key']			
			data_import_info = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']

			body = {
			  "SearchByPartRequest": {
			    "mouserPartNumber": session['symbol']
			  }
			}

			product = mouser_api_call('search/partnumber', key, body)['SearchResults']['Parts'][0]

			# self.write({'files': product_files['Data'], 'parameters': parameters['Data'], 'products': products})
			self.render('store/store.api.importer.mouser.data.hbs',product=product)
