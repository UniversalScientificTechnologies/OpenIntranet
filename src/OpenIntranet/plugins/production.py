#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
import tornado.httputil
from . import Intranet
from . import BaseHandler, BaseHandlerJson
from .store.item_helper import get_items_last_buy_price, create_reservation, get_reservation_components, earse_reservations
#from pyoctopart.octopart import Octopart
import json
import urllib
import bson
import datetime
import pandas as pd
from fpdf import FPDF
from enum import Enum
import math


class round_fpdf(FPDF):
    def rounded_cell(self, w, h=0, txt='', border=0, ln=0, align='', fill=False, link='', radius = 1, corners =  (1,2,3,4), cellspacing = 1):
        style = 'S'
        if fill and border:
            style = 'FD'
        elif fill:
            style = 'F'
        self.rounded_rect(self.get_x() + (cellspacing / 2.0), 
            self.get_y() +  (cellspacing / 2.0),
            w - cellspacing, h, radius, corners, style)
        self.cell(w, h + cellspacing, txt, 0, ln, align, False, link)

    def rounded_rect(self, x, y, w, h, r, corners = (1,2,3,4), style = ''):
        k = self.k
        hp = self.h
        if style == 'F':
            op = 'f'
        elif style=='FD' or style == 'DF':
            op='B'
        else:
            op='S'
        my_arc = 4/3 * (math.sqrt(2) - 1)
        self._out('%.2F %.2F m' % ((x+r)*k,(hp-y)*k ))
        xc = x+w-r 
        yc = y+r
        self._out('%.2F %.2F l' % (xc*k,(hp-y)*k ))
        if 2 not in corners:
            self._out('%.2F %.2F l' % ((x+w)*k,(hp-y)*k ))
        else:
            self._arc(xc + r*my_arc, yc - r, xc + r, yc - r*my_arc, xc + r, yc)
        xc = x+w-r
        yc = y+h-r
        self._out('%.2F %.2F l' % ((x+w)*k,(hp-yc)*k))
        if 3 not in corners:
            self._out('%.2F %.2F l' % ((x+w)*k,(hp-(y+h))*k))
        else:
            self._arc(xc + r, yc + r*my_arc, xc + r*my_arc, yc + r, xc, yc + r)
        xc = x+r
        yc = y+h-r
        self._out('%.2F %.2F l' % (xc*k,(hp-(y+h))*k))
        if 4 not in corners:
            self._out('%.2F %.2F l' % ((x)*k,(hp-(y+h))*k))
        else:
            self._arc(xc - r*my_arc, yc + r, xc - r, yc + r*my_arc, xc - r, yc)
        xc = x+r
        yc = y+r
        self._out('%.2F %.2F l' % ((x)*k,(hp-yc)*k ))
        if 1 not in corners:
            self._out('%.2F %.2F l' % ((x)*k,(hp-y)*k ))
            self._out('%.2F %.2F l' % ((x+r)*k,(hp-y)*k ))
        else:
            self._arc(xc - r, yc - r*my_arc, xc - r*my_arc, yc - r, xc, yc - r)
        self._out(op)

    def _arc(self, x1, y1, x2, y2, x3, y3):
        h = self.h
        self._out('%.2F %.2F %.2F %.2F %.2F %.2F c ' % (x1*self.k, (h-y1)*self.k,x2*self.k, (h-y2)*self.k, x3*self.k, (h-y3)*self.k))



class ComponentStatus(Enum):
    Err = -1 # Nějaká chyba.. 
    Actual = 0  # polozka je nahrana z BOMu
    Obsolete = 1 # Byl nahran novy BOM, ale polozka se v nem nevyskytuje
    ModifiedManually = 2 # Polozka byla rucne upravena
    Failed = 3 # Tohle nastane napriklad v pripade, ze se zmeni UST_ID a hodnota zustane stejna


ComponentStatusTable = {
    ComponentStatus.Err.value: {
        "label": "Chyba určení stavu položky",
        "color": "Gray"
    },
    ComponentStatus.Actual.value: {
        "label": "Položka je načtena z posledního BOMu",
        "color": "green",
    },
    ComponentStatus.Obsolete.value: {
        "label": "Položka může být zastaralá. Nebyla aktualizována při posledním nahrávání BOMu.",
        "color": "orange",
    },
    ComponentStatus.ModifiedManually.value: {
        "label": "Položka byla manuálně upravena",
        "color": "blue",
    },
    ComponentStatus.Failed.value: {
        "label": "Nějaká divnost",
        "color": "gray",
    }

}


def get_plugin_handlers():
        plugin_name = get_plugin_info()["name"]

        return [
             (r'/{}/(.*)/upload/bom/ust/'.format(plugin_name), ust_bom_upload),
             (r'/{}/(.*)/print/'.format(plugin_name), print_bom),
             (r'/{}/(.*)/edit/'.format(plugin_name), edit),
             (r'/{}/(.*)/duplicate/'.format(plugin_name), duplicate),
             (r'/{}/(.*)/get_bom_table/'.format(plugin_name), get_bom_table),
             (r'/{}/(.*)/get_reservation/'.format(plugin_name), get_reservation),
             (r'/{}/api/getProductionTree/'.format(plugin_name), get_production_tree),
             (r'/{}/api/getProductionList'.format(plugin_name), get_production_list),
             (r'/{}/api/productionTree/move/'.format(plugin_name), production_tree_move_elemen),
             (r'/{}/api/productionTree/rename/'.format(plugin_name), production_tree_rename_elemen),
             (r'/{}/api/productionTree/new_folder/'.format(plugin_name), production_tree_new_elemen),
             (r'/{}/api/getProductionGroup/(.*)/'.format(plugin_name), get_production_group),
             (r'/{}/api/updateProductionGroup/(.*)/'.format(plugin_name), update_production_group),
             (r'/{}'.format(plugin_name), home),
             (r'/{}/'.format(plugin_name), home),
        ]

def get_plugin_info():
    return {
        "name": "production",
        "entrypoints": [
            {
                "title": "production",
                "url": "/production",
                "icon": "work"
            }
        ],
        "role": ['sudo', "sudo-production", "production-manager", "production-viewer"]
    }



## Projde seznam vsech komponent v pricelist, a zaktualizuje ceny komponent. Vyuzivaji se ceny posledniho nakupu. 

def production_upadte_pricelist(db, production_id, price_work=-1, price_sell=-1, price_consumables=-1):
    components = db.production.find_one({'_id': bson.ObjectId(production_id)}, {'pricing':1})
    print(components)

    # Zkontroluj, jestli to jiz existuje, pokud ne, tak vytvor cenik
    if 'pricing' not in components:
        components = {
            "count": 0,
            "count_unique": 0,
            "count_ust": 0,
            "count_ust_unique": 0,
            "price_components": 0,
            "price_consumables": float(0),
            "price_work": float(0),
            "price_sell": float(0)
        }
    else:
        components = components['pricing']


    if price_work >= 0:
        components['price_work'] = price_work
    if price_sell >= 0:
        components['price_sell'] = price_sell
    if price_consumables >= 0:
        components['price_consumables'] = price_consumables

    # get last buy price of component
    components_list = []
    comps = list(db.production.find({'_id': bson.ObjectId(production_id)}, {'components':1}))[0]
    for item in comps['components']:
        components["count"] += 1
        uid = item.get("UST_ID", None)
        if uid and bson.ObjectId.is_valid(uid):
            components["count_ust"] += 1
            components_list.append(uid)
            components["price_components"] += get_items_last_buy_price(db, uid)

    components["count_ust_unique"] = len(set(components_list))
    components["price_stock"] = components['price_components'] + components['price_consumables'] + components['price_work']
    components["update"] = 0
    db.production.update_one(
        {'_id': bson.ObjectId(production_id)},
        {'$set':{
            'pricing': components
        }})
    return components


def mask_array(data, mask, default = None):
    new = {}
    for x in mask:
        new[x] = data.get(x, default)
    return new

def num_to_float(data):
    try:
        return float(data)
    except Exception as e:
        return 0

def group_data(data, groupby = ['Footprint', 'UST_ID', 'Value'], db = None):
    selected = []
    for component in data:
        use = 0
        c_ref = [component['Ref']]
        c_footprint = component.get('Footprint', None)
        c_ustid = component.get('UST_ID', None)
        c_value = component.get('Value', 0)
        c_price = num_to_float(component.get('price', 0.0))
        c_component = component.get('store', [])
        print("########")
        print(c_ref)


        s = 0
        for i, sel in enumerate(selected):
            if mask_array(component, groupby) == mask_array(sel, groupby):
                print("Shod..", mask_array(component, groupby), mask_array(sel, groupby))
                selected[i]['Ref'] += c_ref
                selected[i]['count'] += 1
                selected[i]['price_group'] += c_price
                s = 1
                break
        if not s:
            #else: # polozka je zde poprvj
            component['Ref'] = c_ref
            component['count'] = 1
            component['price_group'] = c_price
            price = 0
            print("stav:...", db, c_ustid)
            if db and c_ustid:
                try:
                    o = list(db.stock_movements.find({'product': c_ustid}))
                    print(">...", o)
                    price = o[0].get('price', 0.0)
                except Exception as e:
                    print("ERr", c_ustid)

            component['price_store'] = price
            selected.append(component)


    return selected

# prida do pole pocet skladovych zasob na zaklade nazvu soucastky v dictionary jako 'UST_ID', pokud to neobsahuje, tak je pole preskoceno...
def get_component_stock(data, db):
    for component_i, component in enumerate(data):
        print("____")
        print(component_i, component)
        if component.get('UST_ID', False):
            stock = 0
            movements = db.stock.aggregate([
                {
                    "$match":{'_id': component.get('UST_ID')}
                },{
                    "$unwind": "$history"
                },
            ])
            for movement in movements:
                print(movement)
                stock += movement['history'].get('bilance', 0)
            data[component_i]['stock'] = stock
    return data

class home(BaseHandler):
    def get(self):
        production_list = self.mdb.production.aggregate([])
        self.render('production.home.hbs', production_list = production_list)

'''
    Nacte vsechny polozky z DB pro vytvoreni prehledove tobulky.
'''
class get_production_list(BaseHandlerJson):

    def post(self):
        data = list(self.mdb.production.find())
        for d in data:
            d['id'] = str(d['_id'])
            d['components'] = len(d['components'])
            d['created'] = str(d['created'].date())
            d['author_text'] = ', '.join(d['author'])
            d['placement'] = None
        print(data)
        out = bson.json_util.dumps(data)

        self.set_header("Production-Price", "Je")
        self.write(out)


'''
    Vrátí strom výrobních podkladů
'''
class get_production_tree(BaseHandler):
    role_module = ['production-sudo', 'production-access', 'production-manager', 'production-read']
    def post(self):
        self.set_header('Content-Type', 'application/json')
        type = self.get_argument('type', 'jstree')
        print("api_categories_list .. ", type)

        if type == 'jstree':
            new = []

            # tady se ziskaji stromova struktura
            dout = list(self.mdb.production_tree.find())
            for i, out in enumerate(dout):
                pos = {}
                pos['_id'] = str(out['_id'])
                pos['id'] = str(out['_id'])
                pos['text'] = str(out['text'])
                pos['type'] = 'folder'
                #pos['text'] = "{} <small>({})</small>".format(out['name'], out['description'])
                #pos['text'] = "{} <small>({})</small>".format(out['name'], out['description'])
                #pos['li_attr'] = {"name": out['name'], 'text': out['description']}
                
                pos['parent'] = str(out.get('parent', '#'))
                new.append(pos)


            # tady se ziskaji skupiny
            dout = list(self.mdb.production_groups.find())
            for i, out in enumerate(dout):
                print(i, out)
                pos = {}
                pos['_id'] = str(out['_id'])
                pos['id'] = str(out['_id'])
                pos['text'] = str(out['name'])
                pos['parent'] = str(out.get('parent', "#"))
                #pos['parent'] = "#"
                #pos['icon'] = "jstree-icon jstree-file"
                pos['type'] = 'product'
                new.append(pos)

            output = bson.json_util.dumps(new)

        else:
            self.write("unsupported")

        self.write(output)


class production_tree_move_elemen(BaseHandler):
    def post(self):
        source = bson.ObjectId(self.get_argument('id'))
        destination = self.get_argument('parent')

        validated = True

        if destination != "#":
            destination = bson.ObjectId(destination)

            valid = list(self.mdb.production_tree.find({'_id': destination}))

            if not len(valid):
                print("Nelze presunout, pravdepodobne presouvas spatne")
                self.write("Fail")
                validated = False


        if validated:
            print("Presun production z/do..", source, destination)

            self.mdb.production_tree.update_one( {"_id": source}, {"$set": {"parent": destination}} )
            self.mdb.production_groups.update_one( {"_id": source}, {"$set": {"parent": destination}} )

            self.write("ok")


class production_tree_rename_elemen(BaseHandler):
    def post(self):
        source = bson.ObjectId(self.get_argument('id'))
        new_name = self.get_argument('new_name')

        self.mdb.production_tree.update_one( {"_id": source}, {"$set": {"text": new_name}} )
        self.mdb.production_groups.update_one( {"_id": source}, {"$set": {"name": new_name}} )

        self.write("ok")


class production_tree_new_elemen(BaseHandler):
    def post(self):
        self.mdb.production_tree.insert_one(
            {
                "parent": "#",
                "text": "Nová složka",
                "icon": ""
            }
        )
        self.write("ok")


class get_production_group(BaseHandler):

    # Vytvoreni nove skupiny vyroby
    def get(self, group_id):
        if group_id == 'new':
            new_id = bson.ObjectId()

            self.mdb.production_groups.insert_one(
                {
                    '_id': new_id,
                    'name': "Nová položka výroby",
                    'type': "module",
                    'description': "",
                    'parent': '#'
                }
            )

            self.write(str(new_id))

    def post(self, group_id):
        print(group_id)

        out = self.mdb.production_groups.aggregate([
            {"$match": {"_id": bson.ObjectId(group_id)}},
            {"$lookup": {
               "from": "production",
               "localField": "_id",
               "foreignField": "production_group",
               "as": "series"
             }}
        ])

        self.write(bson.json_util.dumps(out))

class update_production_group(BaseHandler):

    def post(self, group_id):
        group_id = bson.ObjectId(group_id)
        name = self.get_argument('name')
        description = self.get_argument('description')

        self.write("")
            

'''
    Tabulka s BOMem pro zobrazeni v production
'''

class get_bom_table(BaseHandler):
    def get(self, name):

        group_by_ustid = False
        group_by_components = False
    
        query = [
            {'$match': {'_id': bson.ObjectId(name)}},
            {'$unwind': '$components'},
            {'$project': {'components': 1}},
            {'$sort': {'components.Ref': 1}}]

        if group_by_ustid:
            query += [{'$group':{
                '_id': {'UST_ID': '$components.UST_ID'},
                'Ref': {'$push': '$components.Ref'},
                'count': {'$sum': 1},
            }}]
        else:
            query += [{'$group':{
                '_id': {'UST_ID': '$components.UST_ID',
                        'Value': '$components.Value',
                        'Footprint': '$components.Footprint',
                        'status': '$components.status',
                        # 'Distributor': '$components.Distributor',
                        # 'Datasheet': '$components.Datasheet',
                        # 'MFPN': '$components.MFPN',
                        # 'stock_count': '$components.stock_count',
                        # 'note': '$components.note',
                        },
                'Ref': {'$push': '$components.Ref'},
                'count': {'$sum': 1},
            }}]

        query += [{"$addFields":{"cUST_ID": {"$convert":{
                     "input": '$_id.UST_ID',
                     "to": 'objectId',
                     "onError": "Err",
                     "onNull": "null"
            }}}}]
        
        query += [{"$lookup":{
                "from": 'stock',
                "localField": 'cUST_ID',
                "foreignField": '_id',
                "as": 'stock'
            }}]

        query += [{"$lookup":{
                "from": 'packets_count_complete',
                "localField": 'cUST_ID',
                "foreignField": '_id',
                "as": 'packets'
            }}]

        query += [
                {"$sort": {'Ref':1}}
            ]
            
        
        print(query)
        dout = list(self.mdb.production.aggregate(query))
        #out = bson.json_util.dumps(dout)


        self.render('production.bom_table.hbs', data = dout, bson=bson, current_warehouse = bson.ObjectId(self.get_cookie('warehouse')), ComponentStatusTable = ComponentStatusTable)


# Ziskat seznam rezervaci a vratit ho jako HTML tabulku

class get_reservation(BaseHandler):
    def get(self, name):
        name = bson.ObjectId(name)
        components = get_reservation_components(self.mdb, name)
        self.render('production.reservation.hbs', components=components)



'''
   
   EDitační stránka pro production
   
'''
class edit(BaseHandler):
    def get(self, name):
        print("Vyhledavam polozku", name)
        if name == 'new':
            parent = bson.ObjectId(self.get_argument('group'))
            product = self.mdb.production.insert_one({
                    'name': 'Without name',
                    'created': datetime.datetime.now(),
                    'state': 0,
                    'info':{},
                    'author': [],
                    'tags': [],
                    'priority': 0,
                    'type': 'module',
                    'components': [],
                    'production_group': parent
                })
            print(product)
            self.redirect('/production/{}/edit/'.format(product))
        else:
            product = self.mdb.production.aggregate([
                    {'$match': {'_id': bson.ObjectId(name)}}
                ])
            self.render('production.flow.hbs', id = name, product = list(product))

    def post(self, name):
        self.set_header('Content-Type', 'application/json')
        op = self.get_argument('operation', 'get_production')
        print("POST....", op)
        print(name)

        if op == 'get_production':
            #print("get_production")
            dout = list(self.mdb.production.aggregate([
                    {'$match': {'_id': bson.ObjectId(name)}},
                    {'$sort': {'components.Ref': 1}}
                ]))
            print(dout[0])
            output = bson.json_util.dumps(dout[0])
            self.write(output)

        elif op == 'get_components_grouped':

            ###
            ###   V teto casti by se mely zaktualizovat skladove zasoby a url adresy dodavatelu pro vsechny polozky
            ###

            production = list(self.mdb.production.aggregate([
                {'$match': {'_id': bson.ObjectId(name)}},
                {'$unwind': "$components"},
                {'$group':
                    {"_id": "$components.UST_ID", "count": { "$sum": 1 }}
                }
            ]))
            for c in production:
                try:
                    id = c['_id']
                    oid = bson.ObjectId(id)
                    self.component_update_suppliers_url(oid)
                    self.component_update_counts(oid)
                    # count = self.component_get_counts(oid, bson.ObjectId(self.get_cookie('warehouse')))
                    # print(id, "..", count)
                    # if len(count['by_warehouse']) > 0:
                    #     print("Nastavuji", name, id, count['suma'][0]['count'])
                    #     self.mdb.production.update_many(
                    #         {'_id': bson.ObjectId(name), 'components.UST_ID': id},
                    #         {'$set': {"components.$[id].stock_count": count['suma'][0]['count']}},

                    #         array_filters = [{ "id.UST_ID": id}],
                    #         upsert = False
                    #     )
                    # else:
                    #     print("POLOZKA NENALEZENA....")
                except Exception as e:
                    print("CHYBA ....")


            dout = list(self.mdb.production.aggregate([
                    {'$match': {'_id': bson.ObjectId(name)}},
                    {'$unwind': '$components'},
                    {'$project': {'components': 1}},
                    {'$sort': {'components.Ref': 1}},
                    {'$group':{
                        '_id': {'UST_ID': '$components.UST_ID',
                                'Value': '$components.Value',
                                'Footprint': '$components.Footprint',
                                'Distributor': '$components.Distributor',
                                'Datasheet': '$components.Datasheet',
                                'MFPN': '$components.MFPN',
                                'stock_count': '$components.stock_count',
                                'note': '$components.note',},
                        'Ref': {'$push': '$components.Ref'},
                        'count': {'$sum': 1},
                    }},
                    {"$addFields":{"cUST_ID": {"$convert":{
                             "input": '$_id.UST_ID',
                             "to": 'objectId',
                             "onError": "Err",
                             "onNull": "null"
                    }}}},
                    {"$lookup":{
                        "from": 'stock',
                        "localField": 'cUST_ID',
                        "foreignField": '_id',
                        "as": 'stock'
                    }}
                ]))
            out = bson.json_util.dumps(dout)
            print("Get component grouped")
            print(json.dumps(out, indent=4, sort_keys=True))
            self.write(out)

        elif op == 'reload_prices':
            print('Reload prices from stock')


        elif op == 'update_component_parameters':
            print("####.... update_component_parameter")
            component = self.get_arguments('component[]')
            parameter = self.get_argument('parameter').strip().replace('_id.', '')
            value = self.get_argument('value').strip()

            if value == 'undefined': value = ''

            for c in component:
                if parameter == 'UST_ID':
                    value = bson.ObjectId(value)
                    print("JE TO UST ID... budu potrebovat ID")
                self.mdb.production.update_one(
                    {
                       '_id': bson.ObjectId(name.strip()),
                       "components.Ref": c.strip()
                    },
                    {
                        "$set":{"components.$.{}".format(parameter): value}
                    }
                )
                print("Uravil jsem", c)

            print(component, parameter, value)
            out = bson.json_util.dumps({})
            self.write(out)

        elif op == 'update_component':
            print("update_component")

            '''
            tstmp: tstamp,
            ref: ref,
            name: name,
            value: value,
            package: package,
            ust_id: ust_id,
            description: description,
            price_predicted: price_predicted,
            price_store: price_store,
            price_final: price_final
            '''

            ref = self.get_argument('ref')
            value = self.get_argument('value')
            c_name = self.get_argument('name')
            package = self.get_argument('package')
            ust_id = self.get_argument('ust_id')
            price_predicted = self.get_argument('price_predicted', 0.0)
            price_store = self.get_argument('price_store', 0.0)
            price_final = self.get_argument('price_final', 0.0)
            description = self.get_argument('description', '')
            print(ref.split(','))

            for c in ref.split(','):
                exist = self.mdb.production.find({'_id': bson.ObjectId(name), 'components.Ref': c})
                print(exist.count())
                print(bson.ObjectId(name))

                if exist.count() > 0:
                    update = self.mdb.production.update_one(
                            {
                                '_id': bson.ObjectId(name),
                                "components.Ref": c
                            },{
                               "$set": {
                                    "components.$.Ref": c,
                                    "components.$.Value": value,
                                    "components.$.Package": package,
                                    "components.$.UST_ID": ust_id,
                                    "components.$.price_predicted": price_predicted,
                                    "components.$.price_store": price_store,
                                    "components.$.price_final": price_final,
                                    "components.$.Note": description,
                               }
                            }, upsert = True)
                else:
                    print("NOVA POLOZKA")
                    update = self.mdb.production.update_one(
                            {
                                '_id': bson.ObjectId(name)
                            },{
                                "$push": {'components': {
                                    "Ref": c,
                                    "Package": package,
                                    "Value": value,
                                    "UST_ID": ust_id,
                                    "price_predicted": price_predicted,
                                    "price_store": price_store,
                                    "price_final": price_final,
                                    "Note": description
                                    }
                                }
                            })

            dout = [{'state': 'ok'}]
            output = bson.json_util.dumps(dout)
            self.write(output)
        ##
        #### END: Update component
        ##

        elif op == 'update_prices':
            print("UPDATE PRICES ....")
            print(name)
            production = list(self.mdb.production.aggregate([
                {'$match': {'_id': bson.ObjectId(name)}},
                {'$unwind': "$components"},
                {'$group':
                    {"_id": "$components.UST_ID", "count": { "$sum": 1 }}
                }
            ]))

            #print(production)
            #
            # print(production)
            for c in production:
                try:
                    id = c['_id']
                    oid = bson.ObjectId(id)
                    count = self.component_get_counts(oid, bson.ObjectId(self.get_cookie('warehouse')))
                    print(id, "..", count)
                    if len(count['stocks']) > 0:
                        print("Nastavuji", name, id, count['count']['onstock'])
                        self.mdb.production.update_many(
                            {'_id': bson.ObjectId(name), 'components.UST_ID': id},
                            {'$set': {"components.$[id].stock_count": count['count']['onstock']}},

                            array_filters = [{ "id.UST_ID": id}],
                            upsert = False
                        )
                    else:
                        print("POLOZKA NENALEZENA....")
                except Exception as e:
                    print("CHYBA ....", e)
            self.write({'status': 'ok'})




        ##
        #### Update production
        ##
        elif op == 'update_parameters':
            print("update_parameters")
            p_name = self.get_argument('name')
            p_description = self.get_argument('description')
            print(p_name, p_description)

            self.mdb.production.update_one(
                {'_id': bson.ObjectId(name)},
                {'$set':{
                    'name': p_name,
                    'description': p_description
                }})
            dout = [{'state': 'ok'}]
            output = bson.json_util.dumps(dout)
            self.write(output)

        ##
        ### Update pricelist
        ##
        ## aktualizuje cenu teto polozky podle aktualnich nakupnich cen
        ##

        elif op == 'update_pricelist':
            print("Update pricelist")
            components = production_upadte_pricelist(self.mdb, bson.ObjectId(name),
                price_consumables=float(self.get_argument('price_consumables', 0)),
                price_work=float(self.get_argument('price_work', 0)),
                price_sell=float(self.get_argument('price_sell', 0)))
            self.write(components)

        ##
        ### Vytvorit rezervace
        ##
        ##

        elif op == 'do_reservation':
            if not self.mdb.production.find_one({'_id': bson.ObjectId(name)}, {"state": 1})['state'] == 0:
                self.write('{"state": "Nelze vytvořit"}')
                return

            multiplication = float(self.get_argument('count'))
            components_list = []
            comps = list(self.mdb.production.find({'_id': bson.ObjectId(name)}, {'components':1}))[0]
            for item in comps['components']:
                uid = item.get("UST_ID", None)
                if uid and bson.ObjectId.is_valid(uid):
                    components_list.append(uid)

            component_repetition = {}
            for component in set(components_list):
                component_repetition[component] = components_list.count(component)

            for component, repetition in component_repetition.items():
                create_reservation(db=self.mdb, user=self.logged, cid=component,
                    warehouse = self.get_warehouse()['_id'],
                    reservated_count=multiplication*repetition,
                    description="Reservation from production module",
                    origin="production",
                    origin_id=name,
                    flag=["reservation"]
                    )

            # nastavit vyrobu na pripravenou 
            self.mdb.production.update_one({"_id": bson.ObjectId(name)}, {"$set": {"state": 1, "multiplication": multiplication}})

            # take zaktualizuj cenovy rozpis polozky
            production_upadte_pricelist(self.mdb, bson.ObjectId(name))
            self.write('{"state": "ok"}')

        ##
        ### Vymazat rezervace
        ##
        ##

        elif op == 'earse_reservation':
            if self.mdb.production.find_one({'_id': bson.ObjectId(name)}, {"state": 1})['state'] == 1:
                earse_reservations(self.mdb, bson.ObjectId(name))
                self.mdb.production.update_one({"_id": bson.ObjectId(name)}, {"$set": {"state": 0}})
                self.write("")
            self.write('{"state": "Nelze smazat"}')


        ##
        #### Update placement
        ##
        ## Ref,Val,Package,PosX,PosY,Rot,Side
        ##
        elif op == 'update_placement':
            print("update_placement")

            ref = self.get_argument('Ref')
            val = self.get_argument('Val')
            package = self.get_argument('Package')
            posx = self.get_argument('PosX')
            posy = self.get_argument('PosY')
            rot = self.get_argument('Rot')
            side = self.get_argument('Side')
            tstep = self.get_argument('Tstep')

            exist = self.mdb.production.find({'placement.Tstep': tstep})
            print(exist.count())
            print(bson.ObjectId(name))

            if exist.count() > 0:
                update = self.mdb.production.update_one(
                        {
                            '_id': bson.ObjectId(name),
                            "placement.Tstep": tstep
                        },{
                           "$set": {
                                "placement.$.Ref": ref,
                                "placement.$.Tstep": tstep,
                                "placement.$.Val": val,
                                "placement.$.Package": package,
                                "placement.$.PosX": posx,
                                "placement.$.PosY": posy,
                                "placement.$.Rot": rot,
                                "placement.$.Side": side
                           }
                        }, upsert = True)
            else:
                print("NOVA POLOZKA")
                update = self.mdb.production.update_one(
                        {
                            '_id': bson.ObjectId(name)
                        },{
                            "$push": {'placement': {
                                "Tstep": tstep,
                                "Ref": ref,
                                "Val": val,
                                "Package": package,
                                "PosX": posx,
                                "PosY": posy,
                                "Rot": rot,
                                "Side": side
                                }
                            }
                        })

            dout = [{'state': 'ok'}]
            output = bson.json_util.dumps(dout)
            self.write(output)

        elif op == 'add_manufacture_row':
            print("Novy radek pro vyrobu")



            count = self.mdb.production_manufacturing.find({'production': bson.ObjectId(name)}).count()
            sn = "{}{:03n}{}{}".format(str(bson.ObjectId(name))[-4:], count, 19, str(bson.ObjectId(name))[-1:])
            production_id = bson.ObjectId(name)
            date = "Date()"
            author = ""

            data = {
                'production': production_id,
                'sn': sn,
                'state': 0,
                'description':'',
                'history': [],
                #'created': datetime.datetime.now(),
                'creator': author,
            }

            out = self.mdb.production_manufacturing.insert_one(data)
            #out.inserted_id()
            self.write("ok")

        elif op == "get_manufacture_overview":
            data = self.mdb.production_manufacturing.aggregate([
                {'$match': {'production': bson.ObjectId(name)}},
                {'$addFields': {'created': {'$toDate': '$_id'}} },
                {'$addFields': {'created_date':{"$dateToString": {"date": "$_id" }}}  }
            ])
            data = list(data)
            output = bson.json_util.dumps(data)
            self.write(output)

'''
   
   Vytvoř duplikat vyrobniho postupu a nech ho ve stejne slozce
   
'''
class duplicate(BaseHandler):
    def get(self, name):

        name = bson.ObjectId(name)
        product = self.mdb.production.find_one({'_id': name})

        product['_id'] = bson.ObjectId()
        product['name'] += " Duplicate"

        self.mdb.production.insert_one(product)

        print(product)
        self.redirect('/production/{}/edit/'.format(product['_id']))



class ust_bom_upload(BaseHandler):

    def make_comp_dict(self, element):
        print(element)

        tstamp = None
        try:
            tstamp = element.findall('tstamps')[0].text
        except:
            pass

        try:
            tstamp = element.findall('tstamp')[0].text
        except:
            pass

        if not tstamp:
            tstamp = str(bson.ObjectId())

        component = {
                'Tstamp': tstamp,
                "Datasheet": "",
                "Footprint": element.findall('footprint')[0].text,
                "Ref": element.get('ref'),
                "Value": element.findall('value')[0].text,
                "UST_ID": '',
                "stock_count": None,
                "status": ComponentStatus.Actual.value
            }

        update = {x.get('name'):x.get('value') for x in element.findall('property')}

        try:
            component['UST_ID'] = bson.ObjectId(component['UST_ID'])
        except Exception as e:
            pass

        component.update( update )

        return component


    def post(self, name):

        file_dic = {}
        arg_dic = {}

        tornado.httputil.parse_body_arguments(self.request.headers["Content-Type"], self.request.body, arg_dic, file_dic)
        remove_obsolete = int(arg_dic['remove_obsolete'][0])
        # print(file_dic, arg_dic)

        data = file_dic['file'][0]['body']
        #print("file", data)

        from xml.etree import ElementTree
        root = ElementTree.fromstring(data)
        components = root.findall('components')[0]

        # Nastav, ze je polozka zastarala (obsolete)
        self.mdb.production.update_one(
                {"_id": bson.ObjectId(name)},
                {"$set": {"components.$[].status": ComponentStatus.Obsolete.value}})

        for component_xml in components.iter('comp'):
            try:
                print("Nacitani soucastky")
                component = self.make_comp_dict(component_xml)
                print("Component>> ", component)

                exist = list(self.mdb.production.find({'_id': bson.ObjectId(name), 'components.Tstamp': component['Tstamp']}))
                v_update = {}
                v_push = {}


                if len(exist) > 0:
                    print("Update polozky")
                    update = self.mdb.production.update_one(
                            {
                                '_id': bson.ObjectId(name),
                                "components.Tstamp": component['Tstamp']
                            },{
                                "$set": {"components.$": component},
                            })
                else:
                    print("NOVA POLOZKA")
                    component['status'] = ComponentStatus.Actual.value
                    update = self.mdb.production.update_one(
                            {
                                '_id': bson.ObjectId(name)
                            },{
                                "$push": {"components": component},
                            })

            except Exception as e:
                print("Problem s nactenim polozky:", e)

        if remove_obsolete:
            self.mdb.production.update_one(
              { "_id": bson.ObjectId(name) },
              {
                "$pull": { "components": { "status": ComponentStatus.Obsolete.value }},
              });

        self.write("ok")

class print_bom(BaseHandler):
    def get_component(self, components, name, field='Ref'):
        print("get", components, name)
        for c in components:
            print('>>', c)
            if c.get(field, {}) == name:
                return c
        return {}


    def get(self, name):
        info = list(self.mdb.production.aggregate([
            {'$match': {'_id': bson.ObjectId(name)}},
        #     {'$sort': {'components.Ref': 1}},
        #     # {"$lookup":{
        #     #     "from": 'stock',
        #     #     "localField": 'UST_ID',
        #     #     "foreignField": '_id',
        #     #     "as": 'stock'
        #     # }}
        ]))[0]

        print(info)


        out = list(self.mdb.production.aggregate([
                {'$match': {'_id': bson.ObjectId(name)}},
                {'$unwind': '$components'},
                {'$project': {'components': 1}},
                {'$sort': {'components.Ref': 1}},
                {'$group':{
                    '_id': {'UST_ID': '$components.UST_ID',
                            'Value': '$components.Value',
                            'Footprint': '$components.Footprint',
                            'status': '$components.status',
                            #'Distributor': '$components.Distributor',
                            #'Datasheet': '$components.Datasheet',
                            #'stock_count': '$components.stock_count',
                            #'note': '$components.note'
                            },
                    'Ref': {'$push': '$components.Ref'},
                    'category': {'$push': '$components.category'},
                    'count': {'$sum': 1},
                }},
                {"$addFields":{"cUST_ID": {"$convert":{
                         "input": '$_id.UST_ID',
                         "to": 'objectId',
                         "onError": "Err",
                         "onNull": "null"
                }}}},
                {"$lookup":{
                    "from": 'stock',
                    "localField": 'cUST_ID',
                    "foreignField": '_id',
                    "as": 'stock'
                }},
                {"$lookup":{
                    "from": 'packets_count_complete',
                    "localField": 'cUST_ID',
                    "foreignField": '_id',
                    "as": 'packets'
                }},
                {"$lookup":{
                    "from": 'packets_count_complete',
                    "localField": 'cUST_ID',
                    "foreignField": '_id',
                    "as": 'packets'
                }},
                # {"$lookup":{            # tohle nefunguje jak by melo.. 
                #     "from": 'category_complete',
                #     "localField": 'components.stock.category',
                #     "foreignField": '_id',
                #     "as": 'components.stock.category_complete'
                # }},
                {"$sort": {'Ref':1}}
            ]))


        pdf = round_fpdf('P', 'mm', format='A4')
        pdf.set_line_width(0.1)
        pdf.set_draw_color(0,0,0);
        pdf.set_auto_page_break(False)
        pdf.add_font('pt_sans', '', 'static/pt_sans/PT_Sans-Web-Regular.ttf', uni=True)
        pdf.add_font('pt_sans-bold', '', 'static/pt_sans/PT_Sans-Web-Bold.ttf', uni=True)
        pdf.add_page()

        pdf.set_font('pt_sans', '', 12)
        pdf.set_xy(10, 9)
        pdf.cell(0,5, info.get('name', name))

        pdf.set_font('pt_sans', '', 8)
        pdf.set_y(20)
        pdf.cell(0,5, info.get('description', name))

        pdf.set_font('pt_sans', '', 8)
        pdf.set_xy(170, 3)
        pdf.cell(0, 5, "Strana "+str(pdf.page_no())+"/{nb}", border=0)
        pdf.set_xy(170, 6)
        pdf.cell(0, 5, str(datetime.datetime.now())[:16], border=0)
        if pdf.page_no() == 1:
            pdf.set_xy(170, 9)
            pdf.cell(0, 5, "Sklad: {}".format(self.get_warehouse()['name']), border=0)
            pdf.set_xy(10, 13)
            pdf.cell(0, 5, str(name), border=0)

            pdf.set_xy(10, 3)
            pdf.cell(0, 5, "OpenIntranet: {}".format(self.get_company_info()['name']))


        row = []
        used = []

        rowh = 9+8
        rowy = 20
        first_row = 28
        pdf.set_xy(10, 28)

        out = [{
                '_id': {
                    'UST_ID': 'UST_ID',
                    'Value': 'Value',
                    'Footprint': 'FootPrint',
                    'Distributor': 'Distributor',
                    'Datasheet': 'Datasheet',
                    'note': "Poznámka"
                },
                'Ref': ['Ref'],
                'count': '',
                'cUST_ID': "UST_ID",
                'stock': [{'name': 'Název', 'category': ['Kategorie']}]}
            ]+out

        j = 0

        last = 10
        for i, component in enumerate(out):
            print("Component", i)
            item_places = self.component_get_positions(component['cUST_ID'], stock = bson.ObjectId(self.get_cookie('warehouse', False)))

            place_str = ""
            for i, place in enumerate(item_places):
                if place['info'][0]['parent'] is not "#":
                    place_details = self.get_position(place['posid'], True)
                    print(place_details)
                    print(i, "> ", place_details)
                    place_str += " " + place_details['path']
                else:
                    print("###, nema cestu")
                place_str += place['info'][0]['name'] + ", "



            try:
                name = component.get('stock')[0]['name']
                #category = component.get('stock')[0]
                #print(".....CAT", component)
            except Exception as e:
                print("chyba", e)
                name = ''
                category = []

            j += 1
            if rowy > 260:
                j = 0
                rowy = 10
                first_row = 10
                print("New page...")
                pdf.add_page()
                pdf.set_font('pt_sans', '', 8)
                pdf.set_xy(170, 3)
                pdf.cell(0, 5, "Strana "+str(pdf.page_no())+"/{nb}", border=0)
                pdf.set_xy(170, 6)
                pdf.cell(0, 5, str(datetime.datetime.now())[:16], border=0)
                pdf.line(10,first_row, 200, first_row )

                pdf.set_xy(10, 3)
                pdf.cell(0, 5, info.get('name', name), border=0)

            if type(component['count']) == 'String' and ['count'] > 5.0:
                last += 15
            else:
                last += 10

            pdf.set_font('pt_sans', '', 8)

            pdf.set_xy(10, rowy)
            pdf.cell(0, 5, str(i)+'.', border=0)

            pdf.set_xy(15, rowy + 3.5)
            pdf.cell(0, 5, place_str)

            pdf.set_xy(163, rowy)
            pdf.cell(0, 5, str(component['_id'].get('UST_ID', '--')))

            pdf.set_xy(90, rowy + 7)
            pdf.cell(0, 5, component['_id'].get('Footprint', '--')[:30])

            #pdf.set_xy(90, rowy + 7.5)
            #pdf.cell(0, 5, str(component['_id'].get('note', '--')))

            pdf.set_xy(15, rowy+8)
            pdf.cell(0, 5, component['_id'].get('Value', '--')[:30])

            pdf.set_font('pt_sans-bold', '', 7.5)

            pdf.set_font('pt_sans-bold', '', 9)

            pdf.set_xy(15, rowy)
            pdf.cell(0, 5, name)

            pdf.set_font('pt_sans-bold', '', 8)

            pdf.set_xy(15, rowy + 4)
            pdf.cell(0, 5, str(', '.join(component['Ref'])), border=0)

            pdf.set_xy(10, rowy + 4)
            pdf.cell(0, 5, str(component['count'])+'x', border=0)

            pdf.set_font('pt_sans', '', 8)


            pdf.set_xy(15, rowy + 7)
            #pdf.cell(0, 5, str(', '.join(str(category))), border=0)
            #pdf.cell(0, 5, str(category), border=0)


            packet_rount = 0
            for packets in component.get('packets', []):

                pdf.set_line_width(0.1)
                pdf.set_draw_color(110,110,110)
                pdf.set_text_color(110,110,110)

                for packet_i, packet in enumerate(packets.get('packets', [])):
                    packet_rount += 1

                    print(" ")
                    print("packet>", packet)
                    pdf.set_xy(13, rowy+15+packet_i*4)
                    pdf.cell(40, 5, str(packet['packets']['_id']))
                    if len(packet['packets']['position'][0]['path_string']):
                        pdf.cell(90, 5, str(packet['packets']['position'][0]['warehouse']['code']) + " / " + str(packet['packets']['position'][0]['path_string'][0]) + " / " + str(packet['packets']['position'][0]['name']) + " ("+str(packet['packets']['position'][0].get('text', ''))+")")
                    else:
                        pdf.cell(90, 5, str(packet['packets']['position'][0]['warehouse']['code']) + " / " + str(packet['packets']['position'][0]['name']) + " ("+str(packet['packets']['position'][0].get('text', ''))+")")
                    pdf.cell(10, 5, str(packet['packet_count'])+ " ks")

                pdf.rounded_rect(13, rowy+15, 185, 5+packet_i*4, 1)
                pdf.set_line_width(0.01)
                pdf.set_draw_color(0,0,0)
                pdf.set_text_color(0,0,0)

            rowy = rowy + (17 + 6*packet_rount)
            pdf.line(10,rowy-1, 200, rowy-1)
            print("===================Value==========================================", packet_rount)

        pdf.alias_nb_pages()
        pdf.output("static/production.pdf")
        with open('static/production.pdf', 'rb') as f:
            self.set_header("Content-Type", 'application/pdf; charset="utf-8"')
            self.set_header("Content-Disposition", "inline; filename=UST_osazovaci_list.pdf")
            self.write(f.read())
        f.close()
