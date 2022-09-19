from enum import Enum
import datetime
import bson
from .data_import import mouser_api_call
import json


class OrderStatus(Enum):
    NEW = 1
    READY_TO_REVIEW = 2
    REVIEW_DONE = 3
    ORDER_ORDERED = 4
    ORDER_COMPLETE = 5

OrderStatusText = ["Neznámý stav", "Nová objednávka", "Připraveno ke kontrole", "Kontrola splněna", "Objednávka odeslána", "Objednávka dokončena"]


class OrderDirecton(Enum):
    OUTCOMMING = 1
    INCOMMING = 2


def create_empty_order(db):
    order_id = bson.ObjectId()
    content = {
        "_id": order_id,
        "order_status" : OrderStatus.NEW.value,
        "order_supplier" : None,
        "order_supplier_info" : "",
        "total_price" : "",
        "order_identificator": "",
        "payments" : [],
        "items" : [],
        "delivery": [],
        "documents": [],
        "date_created" : datetime.datetime.now(),
        "date_send" : None,
        "direction": OrderDirecton.OUTCOMMING,
    }

    db.orders.insert_one(content)
    return order_id


def order_update_data_from_api(db, order_id):
    print("UPDATE ORDER DATA FROM API...")

    order_data = dict(db.orders.find_one({'_id': order_id}))
    print("ORDER DATA", order_data)
    supplier = order_data.get('order_supplier', None)

    if supplier.lower() == 'mouser':
      key = db.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']['mouser_api_key_account']           
      #data_import_info = self.mdb.intranet_plugins.find_one({'_id': 'store'})['data']['data_import']

      body = {}

      order_info = mouser_api_call('order/{}'.format(order_data.get('order_identificator')), key, body, method="GET")
      return order_info