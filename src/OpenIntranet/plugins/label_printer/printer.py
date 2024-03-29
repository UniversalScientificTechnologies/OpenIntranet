#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
from .. import Intranet
from .. import BaseHandler
from ..store.packet_helper import get_packet
import json
import bson.json_util
import urllib
import datetime
import json
import code128

from fpdf import FPDF
from bson import ObjectId
from plugins import BaseHandler
from pystrich.datamatrix import DataMatrixEncoder

class print_label_default(BaseHandler):
    def get(self):
        print("Tisk home page   ...")
        self.render('print.home.hbs')


class print_packet_list(BaseHandler):

    def get(self):
        print("Tisk home page   ...")
        self.render('print.home.hbs')

class print_label(BaseHandler):

    def gen_pdf(self, data):

            a4_w = 210
            a4_h = 297

            pdf = FPDF('P', 'mm', (a4_w, a4_h))
            pdf.set_auto_page_break(False)

            pdf.add_font('pt_sans', '', 'static/pt_sans/PT_Sans-Web-Regular.ttf', uni=True)
            pdf.add_font('pt_sans-bold', '', 'static/pt_sans/PT_Sans-Web-Bold.ttf', uni=True)
            pdf.set_font('pt_sans', '', 11)
            pdf.add_page()
            page = 0
            skip = 0
            warehouse_name = self.get_warehouse().get('name', "Neni nastaven")

            for i, label in enumerate(data):
                #print(".....")
                #print(label)
                pdf.set_text_color(0)

                ir = i + skip   # cislo bunky
                ip = ir%(3*7)   # cislo bunky na strance
                row  = ip//3    # cislo radku
                cell  = ip%3    # cislo sloupce
                actual_page = ir//(3*7) # cislo stranky
                #print(i, ir, ip, row, cell)
                if page != actual_page:
                    print("NOVA STRANKA", actual_page)
                    pdf.add_page()
                    page = actual_page

                #x0 = 70*cell
                #y0 = (297/7)*row

                label_width = 69.7
                label_height = 42

                x0 = a4_w/2 + (-1.5+cell) * label_width
                y0 = a4_h/2 + (-3.5+row) * label_height + 2
                
                id = str(label['id'])
                printed_id = id



                if label['type'] == 'packet':
                    packet = label['packet']

                    pdf.set_text_color(150)
                    pdf.set_font('pt_sans', '', 6)
                    pdf.set_xy(x0+4, y0+1)
                    pdf.cell(label_width-8, 4.5, "Packet", align = 'L')


                    # nazev soucastky
                    
                    pdf.set_draw_color(10)
                    pdf.set_fill_color(245)
                    pdf.set_text_color(0)

                    pdf.set_font('pt_sans-bold', '', 12)
                    pdf.set_xy(x0+5, y0+4.5)
                    

                    label_name = label['component']['name']
                    if len(label_name) > 40:
                        label_name = label_name[40:]+".."
                    name_length = pdf.get_string_width(label_name)

                    if name_length > 58:
                        for size in range(0, 70):
                            pdf.set_font('pt_sans-bold', '', 12-size/10)
                            name_length = pdf.get_string_width(label_name)
                            if name_length < 58:
                                print("Zmenseny nazev, velikost", 12-size/10)
                                break
                    print("DELKA:", pdf.get_string_width(label_name), label_name)
                    pdf.cell(label_width-10, 4.5, label_name, align = 'L', border=1)


                    pdf.set_font('pt_sans', '', 8)

                    ## print(label.keys())
                    id = str(label['_id'])

                    barcode = "[)>\u001E06"     # format 06 header
                    barcode += "\u001DS{}".format(label['id'])  ## Sacek
                    #barcode += "\u001D1P{}".format(label['component']['_id'])       # component identificator by supplier
                    # barcode += "\u001D30P{}".format(label['component']['name'])    # Component identificator by supplier - 1st level
                    barcode += "\u001D5D{}".format(datetime.datetime.now().strftime("%y%m%d"))
                    barcode += "\u001E\u0004"   # end of barcode
                    encoder = DataMatrixEncoder(barcode)
                    encoder.save("static/tmp/barcode/%s.png"%(id))

                    pdf.set_xy(x0+label_width-20-4, y0+8+7)
                    pdf.image('static/tmp/barcode/%s.png'%(id), w = 20, h=20)

                    # Popis stitku
                    pdf.set_text_color(20)
                    pdf.set_font('pt_sans', '', 8)

                    description = label['component'].get('description', '')[:110].strip()
                    pdf.set_xy(x0+4, y0+15)
                    pdf.multi_cell(label_width-28, 2.8, description, align='L', border=0)

                    # pozice ve skaldu, oznaceni stitku uzivatelskym kodem
                    pdf.set_text_color(0)
                    pdf.set_xy(x0+label_width-19, y0+10)
                    pdf.set_font('pt_sans-bold', '', 9)
                    pdf.cell(14, 5, label['packet']['name'], align="R", fill=True)


                    pdf.set_text_color(80)
                    pdf.set_xy(x0+5, y0+10)
                    if "warehouse" in label:

                        pos = "/"
                        for p in reversed(label['path']):
                            pos += p['name'] + "/"

                        pos += label['position']['name']
                        pdf.set_font('pt_sans-bold', '', 9)
                        pdf.multi_cell(label_width-29, 3, pos, align='L')


                        pdf.set_font('pt_sans', '', 8)
                        pdf.set_text_color(80)
                        pdf.set_xy(x0+32, y0+32)
                        pdf.cell(14, 3.5, label['warehouse']['code'].upper(), align="R")

                    else:
                        pdf.set_text_color(120)
                        pdf.set_font('pt_sans', '', 10)
                        pdf.write(5, "Mimo skladu")

                    cat_text = ""
                    if "category" in label:
                        pos = []
                        cat_text = " | cat: "
                        for c in label['category']:
                            pos += [c['name']]

                        cat_text += ','.join(pos)

                    pdf.set_font('pt_sans', '', 9)
                    pdf.set_text_color(60)
                    pdf.set_xy(x0+4, y0+34.5)
                    pdf.cell(0, 0, "{} ks".format(packet['packet_count']), align="L")
                    printed_id = packet['_id']


                    # Zkus najit dodavatele sacku. Pokud to nejde, nevadi.. proste tam nic nebude 
                    try:
                        supplier_order = int(packet['supplier'])
                        supplier_info = packet['component'][0]['supplier'][supplier_order]
                        supplier_text = supplier_info.get('supplier', "NA") + " | " + supplier_info.get('symbol', "NA")
                        
                        pdf.set_font('pt_sans', '', 8)
                        pdf.set_text_color(100)
                        pdf.set_xy(x0+4, y0+29)
                        pdf.cell(label_width-28, 4.5, supplier_text, align = 'L', border=0)
                    except:
                        pass


                if label['type'] == 'position':
                    #packet = label['packet']
                    position = label['position_label']

                    ## Vzhled pozic
                    pdf.set_fill_color(220,255,220)
                    pdf.rect(x0+1, y0+1, w=label_width-2, h=label_height-2, style = 'F')

                    pdf.set_fill_color(100,220,100)
                    pdf.rect(x0+5, y0+4.5, w=label_width-10, h=4.5, style = 'F')


                    pdf.set_text_color(100)
                    pdf.set_font('pt_sans', '', 6)
                    pdf.set_xy(x0+4, y0+1)
                    pdf.cell(label_width-8, 4.5, "Pozice", align = 'L')

                    pdf.set_text_color(0)
                    pdf.set_font('pt_sans-bold', '', 12)
                    pdf.set_xy(x0+5, y0+4.5)
                    pdf.cell(label_width-10, 4.5, position['position']['name'][:25], align = 'L', border=1)


                    pdf.set_xy(x0+4, y0+16)
                    pdf.set_font('pt_sans', '', 12)
                    #pdf.write(5, position['position']['text'])
                    pdf.multi_cell(label_width-28, 5, position['position']['text'][:80], align='L')

                    barcode = "[)>\u001E06"     # format 06 header
                    barcode += "\u001D1L{}".format(id)  ##   Pozice
                    #barcode += "\u001D1P{}".format(label['component']['_id'])       # component identificator by supplier
                    #barcode += "\u001D5D{}".format(datetime.datetime.now().strftime("%y%m%d"))
                    barcode += "\u001E\u0004"   # end of barcode
                    encoder = DataMatrixEncoder(barcode)
                    encoder.save("static/tmp/barcode/%s.png"%(id))

                    pdf.set_xy(x0+label_width-20-4, y0+8+7)
                    pdf.image('static/tmp/barcode/%s.png'%(id), w = 20, h=20)
                    pdf.set_font('pt_sans', '', 6)
                    pdf.set_text_color(100)
                    pdf.set_xy(x0+0, y0+7)
                    # pdf.cell(65, 0, , align = 'R')


                    # Cesta


                    pdf.set_xy(x0+4, y0+10)
                    pdf.set_font('pt_sans', '', 10)
                    pdf.write(5, position['position']['warehouse']['code'].upper())
                    pdf.set_font('pt_sans', '', 12)
                    path = '/'.join((position['position']['path_string']))
                    if len(path) > 0:
                        path = "/" + path
                    pdf.write(5, path)
                    # pdf.set_font('pt_sans-bold', '', 12)
                    # pdf.write(5, position['position']['name'])

                    # pdf.set_xy(x0+4, y0+10)
                    # pdf.set_font('pt_sans-bold', '', 10)
                    # path = position['position']['warehouse']['code'].upper() + "/" + path
                    # pdf.multi_cell(70-28, 2.8, path, align='L')

                    # pozice ve skaldu

                    pdf.set_text_color(100)
                    pdf.set_xy(x0+4, y0+8.8)

                    print(">>>")
                    print(label)



                else:
                    pass

                pdf.set_text_color(100)
                pdf.set_font('pt_sans', '', 7)
                pdf.set_xy(x0, y0+37)
                pdf.cell(label_width, 0, "UST.cz|{}|{}".format(datetime.datetime.now().strftime("%d.%m. %Y,%H:%M"), printed_id), align="C")


            task = "tisk"

            pdf.output('static/tmp/{}.pdf'.format(task), 'F')
            gen_time = datetime.datetime(2018, 10, 1)
            lastOid = ObjectId.from_datetime(gen_time)


            self.redirect('/static/tmp/{}.pdf'.format(task))


    def get(self):

        print("Tisk stitky...")

        groups = self.get_arguments('group[]')
        for i, g in enumerate(groups):
            if g == "None": groups[i] = None
            else: groups[i] = ObjectId(g)

        print("Mam tisknout skupiny", groups)

        labels = list(self.mdb.label_list.aggregate([
            {"$match": {"group" : {"$in" : groups}}},
            {
               "$lookup": {
                   "from": 'stock',
                   "localField": 'id',
                   "foreignField": 'packets._id',
                   "as": 'component',
               }
            },
            {"$set": { "component": { "$first": "$component" }}   },

            {
              "$lookup":
                 {
                   "from": "stock",
                   "let": { "packet": "$id"},
                   "pipeline": [
                      { "$unwind": '$packets'},
                      { "$match": { "$expr": { "$eq": ["$packets._id", "$$packet"]} }},
                      { "$replaceRoot": {"newRoot": "$packets"}},
                   ],
                   "as": "packet"
                 }
            },
            {"$set": { "packet": { "$first": "$packet" }} },

            {
               "$lookup": {
                   "from": 'store_positions',
                   "localField": 'packet.position',
                   "foreignField": '_id',
                   "as": 'position',
               }
            },
            {"$set": { "position": { "$first": "$position" }} },

            {
               "$graphLookup": {
                  "from": 'store_positions',
                  "startWith": '$position.parent',
                  "connectFromField": "parent",
                  "connectToField": "_id",
                  "as": 'path'
               }
            },

            {
               "$lookup": {
                   "from": 'warehouse',
                   "localField": 'position.warehouse',
                   "foreignField": '_id',
                   "as": 'warehouse',
               }
            },
            {"$set": { "warehouse": { "$first": "$warehouse" }} },


            {
               "$lookup": {
                   "from": 'category',
                   "localField": 'component.category',
                   "foreignField": '_id',
                   "as": 'category',
               }
            },
            {
               "$graphLookup": {
                  "from": 'store_positions',
                  "startWith": '$category.parent',
                  "connectFromField": "parent",
                  "connectToField": "_id",
                  "as": 'path_cat'
               }
            },


# POZICE


            {
               "$lookup": {
                   "from": 'store_positions_complete',
                   "localField": 'id',
                   "foreignField": '_id',
                   "as": 'position_label.position',
               }
            },
            {"$set": { "position_label.position": { "$first": "$position_label.position" }} },


        ]))


        for i, label in enumerate(labels):

            if label['type'] == 'packet':
                labels[i]['packet'] = get_packet(self.mdb, label['id'])

        #print(labels)
        self.gen_pdf(labels)
        #self.write(bson.json_util.dumps(labels))
        # self.render('print.label.hbs', print_task = dbobject)



class generate_label(BaseHandler):
    def get(self):

        task = self.get_argument('task', None)
        skip = int(self.get_argument('skip', 0))
        if task:
            print(task)
            task_data = self.mdb.label_generation.find_one({'_id': ObjectId(task)})
            print(task_data)
            group = task_data['type']
            items = task_data['items']
        else:
            data = self.get_argument('data', None)
            group = self.get_argument('group', None)

        if group == 'labels':

            length = len(items)

            items = list(self.mdb.store_labels.find({
              "_id" : {"$in" : items }
            }))


            pdf = FPDF('P', 'mm', format='A4')
            pdf.set_auto_page_break(False)

            pdf.add_font('pt_sans', '', 'static/pt_sans/PT_Sans-Web-Regular.ttf', uni=True)
            pdf.add_font('pt_sans-bold', '', 'static/pt_sans/PT_Sans-Web-Bold.ttf', uni=True)
            pdf.set_font('pt_sans', '', 12)
            pdf.add_page()
            page = 0

            warehouse_name = self.get_warehouse().get('name', "Neni nastaven")

            for i, label in enumerate(items):
                pdf.set_text_color(0)

                ir = i + skip
                ip = ir%(3*7)
                row  = ip//3
                cell  = ip%3
                print(i, ir, ip, row, cell)
                if page != (ir//(3*7)):
                    print("NOVA STRANKA", ir//(3*7))
                    pdf.add_page()
                    page = ir//(3*7)

                x0 = 70*cell
                y0 = (297/7)*row

                #pdf.set_draw_color(231, 221, 25)
                pdf.set_fill_color(231, 121, 25)
                pdf.set_xy(x0, y0+4)
                pdf.rect(x0, y0+12.5, w=70, h=8.4, style = 'F')

                pdf.set_font('pt_sans-bold', '', 14)
                pdf.set_xy(x0, y0+8.5)
                pdf.cell(70, 0, label['name'][:25], align = 'C')

                pdf.set_font('pt_sans', '', 11)
                pdf.set_xy(x0+3.5, y0+13.5)
                pdf.multi_cell(70-4, 3.4, label['text'], align='L')

                pdf.set_text_color(100)
                # pdf.set_font('pt_sans', '', 8)
                # pdf.set_xy(x0+2, y0+2.5)
                # pdf.cell(70, 0, "Pozice: {}".format(warehouse_name))

                id = str(position['_id'])

                barcode_content = "[)>\u001E06\u001DL{posID}\u001DT{packetId}\u001D1P{componentId}\u001D5D{Date}\u001E\u0004".format(posID = "", packetId = id, componentId = "", Date = "20200101")
                encoder = DataMatrixEncoder(a)
                encoder.save("static/tmp/barcode/%s.png"%(id))


                pdf.set_font('pt_sans', '', 7)
                pdf.set_xy(x0, y0+30)
                pdf.cell(70, 0, barcode, align = 'C')

                pdf.set_font('pt_sans', '', 7)
                pdf.set_xy(x0+3.5, y0+33)
                pdf.cell(70, 0, "{} | {}".format(warehouse_name, datetime.datetime.now().strftime("%d. %m. %Y, %H:%M")))


                print(label['category'])


            pdf.output('static/tmp/{}.pdf'.format(task), 'F')

            gen_time = datetime.datetime(2018, 10, 1)
            lastOid = ObjectId.from_datetime(gen_time)

            print(self.get_warehouse())

            self.write('/static/tmp/{}.pdf'.format(task))

        else:
            self.write("OK")
