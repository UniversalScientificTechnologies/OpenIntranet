Celý systém je naprogramovaný v Python3 a je postavený na databázovém systému mongodb.


## Instalace
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

## Spuštění
```bash
python3 web.py --config=/data/intranet.conf 
```
