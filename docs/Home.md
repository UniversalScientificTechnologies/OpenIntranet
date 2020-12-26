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




## Závislosti
```
sudo apt install python3-mongoengine python3-hashids
sudo pip3 install pyocclient fpdf python-barcode code128 gitpython pandas
```

