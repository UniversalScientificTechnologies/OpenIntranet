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

        print("...")

        group = {
            '_id': ObjectId(),
            'name': production['name'],
            'type': 'module',
            'description': production['description'],
            'parent': production['parent'],
        }

        production = {
            "$set": {"parent", group['_id']},
            "$set": {"component": None}
        }

        db.production_groups.insert_one(group)
        db.production.update({"_id": production['_id']}, production)



    except Exception as e:
        print(e)

print(i, "celkem mame polozek")
print(n, "upraveno polozek")
