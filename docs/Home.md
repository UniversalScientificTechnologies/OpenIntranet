OpenIntranet je open-source software pro potřeby řízení firmy a jejích potřeb. Aplikace je založená na webovém frameworku '''tornado'''. Díky uživatelského rozhraní formou webu je možné tento systém používat na všech běžných operačních systémech pouze v moderním webovém prohlížeči. Systém je založen na principu pluginů, kdy každý nabízí jiné, potřebné, operace.

# Popis aktuálních modulů

## Modul sklad

Modul sklad slouží k základním úpravám položek v databázi skladu.

Modul je rozdělen do dvou sloupců. V pravém sloupci je seznam všech položek, které odpovídají zvolenému filtru. V levém sloupci je detail aktuálně vybrané položky, vyhledávání a filtrování položek a nástroje pro tisk štítků a tiskových sestav.

### Seznam položek
Seznam modulů nyní podporuje dva režimy. Jeden 'standartní' a druhý 'inventura'.

Standartní režim slouží k prohlížení seznamu. Obsahuje informace jako název položky, její ID, popis.

Dalším režimem je 'inventura'


### Detail položky
Detail položky zobrazuje veškeré informace o aktuálně načtené položce. Pokud je položka v pravém sloupci, je žlutě zvýrazněna.















## Databáze
Systém využívá NoSQL databázi MongoDB.


##### Položky skladu
```ejson
{
  "_id": "nazev_polozky",                     // unikátní název položky, měl by obsahovat pouze základní znaky
  "aid": {                                    // Alternativní kódy položky
      "id_00001":{                                
          "code": 1,
          "type": "CODE128",
          "supplier": "eshop"
      }
  },
  "name": "Název položky",                    // Název položky, může používat UTF-8 znaky
  "category": ["cat_id"],                     // Kategorie položky
  "type": 0,                                  // typ položky, 0: standartní položka skladu, 1: jednorázová položka,
                                                  // 2: stará položka/odstranění, 3:
  "description": "Informace o položce",       // Delší popis položky
  "price": 000.00,                            // poslední nákupní cena
  "supplier": [                               // dodavatelé
      {"name": "eshop"}
  ],
  "stock": {                                  // Skladové zásoby
      "PHA01":{"count": 353},
      "PHA02":{"count": 353}
  },
  "tags": {
      "inventura":{
          "display": None,
          "date": ISODATE(xx-xx-xxxTyy:yy:yy),
          "autor": None,
          "type": "success",
      },
      "standard": {
          "display": True,
          "date": ISODATE(xx-xx-xxxTyy:yy:yy),
          "autor": None,
      }
  },
  "parameters":{                              // Parametry součástky, na základě nich bude doděláno filtrování
    "m_u":{
      "value":3553,
    },   
  }
}
```


```ejson
{
  "_id": ObjectID(),
  "component": "id_polozky"
  "operation": "operace",                       // Co je s položkou provedeno ["buy", "sell", "use", "inventura"]
}
```


## Závislosti
```
sudo apt install python3-mongoengine python3-hashids
sudo pip3 install pyocclient fpdf python-barcode code128 gitpython pandas
```

