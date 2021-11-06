---
layout: default
title: Production
nav_order: 2
parent: Moduly
has_children: true
permalink: modules/production
---


# Popis

Modul production je navržen a vyvinut pro výrobu elektronických komponent. Užvatel si ze svého oblíbeného CAM programu vygeneruje BOM a ten nahraje do intranetu do sekce production. Následně provede spárování komponent v BOMu se součástkami ve skladu. Sekce production uživatele upozorní na skladové zásoby potřebných součástek. 





# Vytváření KiCad XML netlistu

Otevřete v KiCADu schéma, ze kterého chcete netlist vytvořit. Klikněte `Soubor -> exportovat -> Exportovat Netlist ..`. Při prvním použití klikněte `Přidat generátor`. Napište název generátoru a pak klikněte `Procházet generátory`. Zde vyberte `Kicad`. Uložte tento generátor a vraťte se do okna `Exportovat Netlist`. V horní části se vytvoří nová záložka. Na tu klikněte a dejte `Exportovat netlist`. Nyní budete vyzván pro výběr složky, kam se má netlist. uložit. 



***
# pracovní texty


## Stavy při výrobě
```
0 Plánováno
1 Rezervováno
2 Výroba
3 Vyrobeno
4 Před testováním
5 Test OK
6 Test Fail
7
8
9
10 Dokončeno
```
