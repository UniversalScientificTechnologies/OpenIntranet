---
layout: default
title: Store - Warehouse management system
nav_order: 0
parent: Moduly
has_children: true
permalink: modules/store
---


# Modul ```sklad```

Modul sklad slouží pro agendu ohledně správy skladu a skladových zásob. 

Nejmenší skladová entita je sáček obsahující určitý počet identických součástek. 

## Schopnosti
 * Vytvářet skladové položky
 * Duplikovat skladové položky
 * Přehled všech skladových zásob
 * Rozdělování na sáčky


## Seznam skladových položek
V seznamu skladových položek můžete nalézt přehled všech skladových položek. Můžete v nich vyhledávat nebo si je prohlížet dle skladových kategorií. 
![store_view](https://user-images.githubusercontent.com/5196729/144079223-7115499f-46e5-4d75-87d5-1a0b965e921c.png)


## Editace názvu součástky 

Název položky se edituje dvojklikem na samotný název. Pak se otevře takové okno (tzv. modal).

![Component name change](https://raw.githubusercontent.com/UniversalScientificTechnologies/OpenIntranet/master/doc/img/item_name_edit.png)


## Access rights

 | Označení | Název | Popis | 
 |----------|-------|-------|
 | ```stock-sudo``` | Správce skladu | Kompletní přístup ke všem funkcím skladu. Včetně možnosti pokročilé editace |
 | ```stock-manager``` | Manažer skladu | Stará se o chod skladu, může vytvářet nové součástky, provádět všechny skladové operace včetně nákupu a podobných záležitostí. |
| ```stock-user``` | Uživatel skladu | Uživatel může pouze prohlížet sklad a dělat některé operace. Například servisní odběr. Uživatel nevidí některé citlivé údaje. Jako dodavatel nebo ceny nákupů. Má přístup ke skladovým počtům.| 
| ```stock-guest``` | Návštěvník skladu | Nemůže provádět žádné skladové operace. Pouze přístup k necitlivým údajům.|


