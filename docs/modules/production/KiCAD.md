---
layout: default
title: Production - Kicad
nav_order: 0
parent: Production
grand_parent: Moduly
has_children: true
permalink: modules/production/kicad
---


Intranet umí základním způsobem zpracovávat datové výstupy z KiCADu.  Potřebuje k tomu znát identifikátor součástky ve skladu. Tento identifikátor je aktuálně zadáván uživatelem v podobě speciálního pole UST_ID zadaného v parametrech součástky.

![Component identification](https://raw.githubusercontent.com/UniversalScientificTechnologies/OpenIntranet/master/doc/img/OpenIntranet_component_ID.png)

V současné implementaci je nutné manuálně udržovat korektní UST_ID vzhledem k hodnotě a typu zvolené součástky. [viz issue](https://github.com/UniversalScientificTechnologies/OpenIntranet/issues/150)
