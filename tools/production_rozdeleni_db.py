from pprint import pprint
import csv
import pymongo
import json
import urllib.request
import re
import sys
import datetime
from bson import ObjectId
import hashids
from hashlib import blake2b, blake2s
import time

client = pymongo.MongoClient('localhost', 27017)
db = client.USTdev

productions = list(db.production.find())
n = 0

for i, production in enumerate(productions):
    try:

        print("...", production['_id'])

        group = {
            '_id': ObjectId(),
            'name': production['name'],
            'type': 'module',
            'description': production.get('description', ''),
            'parent': "#",
        }

        production_update = {
            "$set": {"production_group": group['_id'], "component": None}
        }
        
        db.production_groups.insert_one(group)
        db.production.update_one({"_id": production['_id']}, production_update)

    except Exception as e:
        print("chyba", e)

print(i, "celkem mame polozek")
print(n, "upraveno polozek")
