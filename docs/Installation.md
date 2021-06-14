Celý systém je naprogramovaný v Python3 a je postavený na databázovém systému mongodb.


## Instalace
 * Vytvořit si klon repozitáře (nebo stáhnout release)
 * Nanistalovat mongodb databázi podle oficiálního návodu (Verze > xxx) 
 * Nainstalovat python3 a knihovny z [requirements.txt](https://github.com/UniversalScientificTechnologies/OpenIntranet/blob/master/requirements.txt) - Seznam díky aktivnímu vývoji nemusí být vždy aktuální. 


## Konfigurace

konfigurace.conf:
```
port = 11111
debug = True

owncloud_url = 'http://owncloud.mujsklad.cz'
owncloud_user = 'owncloud_user'
owncloud_pass = 'owncloud_Pass'
owncloud_root = 'intranet'
mdb_database = 'IntranetDB'

intranet_name = 'OpenIntranet'
intranet_url = 'https://mujsklad.cz'
intranet_storage = '/data/intranet_storage'

plugins = ['', 'store','system', 'stocktaking', 'stocktaking_view_positions', 'production', 'label_printer', 'order_incoming', 'cart', 'base_info','users', 'order_incoming']
```

## Inicializace databáze

### sklad

Je potřeba v databázi vytvořit položku skladu. A pak tento sklad nastavit jako výchozí. 

V kolekci `warehause` vytvořit položku:
```
{
    "code" : "...zkratka_skladu...",
    "name" : "...celý_nazev_skladu...",
    "address" : "....adresa_skladu..."
}
```

K tomu se vytvoří _id. To je potřeba vepsat do následujícího dokumentu s id `default_warehouse`. 

kolekce databáze `intranet` by měla obsahovat:
```
{
    "_id" : "company_info",
    "name" : "...company_name...",
    "address" : "...company_address...",
    "crn" : "...company registration number - ID..."
}
{
    "_id" : "dpp_params",
    "year_max_hours" : 300,
    "month_max_gross_wage" : 10000,
    "tax_rate" : 15,
    "tax_deduction" : 2070,
    "tax_deduction_student" : 335
}
{
    "_id" : "default_warehouse",
    "*" : ObjectId("..default_warehouse_id...")
}
```

* code - zkrácený název skladu využívaný k zobrazení v systému
* name - je celý dlouhý název skladu
* address - je lokace skladu


### sklad

Nově vytvořený uživatel z webového rozhraní nemá žádná práva. Ty je potřeba ručně nastavit v DB - pak to lze provádět přes UI. Ale potíž instalece je předpoklad, že už takový uživatel exesituje. 

U uživatele je ještě potřeba nastavit pole
 * prázdné `workpans` (bug #114)
 * Pro začátek lze nastavit tato oprávnění:

```
[
    "sudo",
    "sudo-store",
    "sudo-users",
    "sudo-import",
    "invoice-access",
    "invoice-create",
    "invoice-reciever"
]
```

Je potřeba obojí zatím ručně nastavit v databázi. U uživatele mu stanovit oprávnění a nastavit výchozí sklad.

Pro tato nastavovaní by bylo užitečné mít nějaký bash/python skript. 

## Spuštění

```bash
python3 web.py --config=/data/intranet.conf 
```
