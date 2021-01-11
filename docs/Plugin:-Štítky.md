Pro tvorbu štítků existuje samostatný plugin, který shlukuje jednotlivé štítky do skupin. Jednotlivé skupiny slouží k tisku a k tvorbě tiskových sestav na archy samolepek. Systém zná několik typů štítků, které se liší dle obsahu a užití. 



## Čárové kódy

Na štících může být užito několik typů čárových kódů. 

V možných případech je preferováno ve štítkách uživat standardy:
 * [ECIA - Labeling Specification for Product and ShipmentIdentificationin the Electronics Industry](https://www.ecianow.org/assets/docs/GIPC/EIGP-114.2018%20ECIA%20Labeling%20Specification%20for%20Product%20and%20Shipment%20Identification%20in%20the%20Electronics%20Industry%20-%202D%20Barcode.pdf)
 * [Format 06 ISO/IEC 15434](https://static.spiceworks.com/attachments/post/0016/2204/data_dictionary.pdf)
 * Format DD 

Obecný popis o standardu [ISO/IEC 15434 Barcode Specifications](https://www.barcodefaq.com/2d/data-matrix/iso-iec-15434/)

### 1D Code 128

Tento typ byl jeden z prvních pokusů o čárové kódy využívané v intranetu, jeho nevýhodou je vysoká optimalizace především pro číselné stringy při použití na jiné znaky se kód stává rychle neefektivní. 


### 2D Datamatrix

[data Matric code](https://en.wikipedia.org/wiki/Data_Matrix)


#### Obsah a význam dat 

| Kód | Zkratka | Název | Význam |
|-----|---------|-------|--------|
| L   | Loc     | Location | Obecná pozice - OID pozice umístění sáčku |
| 20L | 1Loc | First Level (internally assigned) | Sklad (Uživatelsky čitelný sklad) |
| 21L | 1Loc | *** Level (internally assigned) | Pozice ve skladu (Cesta pozice ve skladu) |
| 22L | 1Loc | *** Level (internally assigned) | -- |
| 23L | 1Loc | *** Level (internally assigned) | -- |
| 24L | 1Loc | Fift Level (internally assigned) | -- |
| T | LOT | | Sáček - u součástek to může mít význam sarže (do sloučení) |
| 3Z | | Free Text | Vlastní popis |
| 10Z| | Structured Free Text  (Header Data) | |
| 11Z - 99Z | | Structured Free Text (Line 1-89 Data) | |

### Formát a datová struktura
```
[)><RS>06<GS>17V98897<GS>1P4L0014-163B<GS>SSA10197<RS><EOT>
```

Kód se skládá ze tří částí: Hlavičky, dat a patičky. 

Hlavička: `[)><RS>06`, kde `06` značí typ datového formátu 'Format 06'. 
Data: Data jsou uvedena kódem, který se skládá z `<GS>`, maximálně dvou čísel a jednoho písmene. Následuje samotný obsah. 
Patička: zpráva končí neviditelnými znaky `<RS><EOT>`

## RFID čipy 

Při konstrukci skladového systému zvažujeme i možnost použití RFID čipů, zejména variant čitelných NFC čtečkou v mobilních telefonech. 
Jejich použití by pak vypadalo obdobně, jako použití tištěných štítků, ale byly by hozené uvnitř sáčku, nebo nalepeny na zařízení. 

Potenciální výhody oproti použití tištěných štítků jsou tyto: 

* Možnost recyklace (NFC tag lze použít opakovaně pro různé skladové položky)
* NFC čip může nést některé informace i bez přímého přístupu do databáze (Například informaci o vypůjčení a komu se předmět má vrátit, nebo jaká je aktuální expirace)
* RFID čip lze využít k dohledání položek ve vymezeném prostoru (nopříklad v krabici, na stole a podobně)


# Typy štítků

## Packet (Sáček)
Data:
* Packet ID 
* Pozice sáčku

### Štítek: 7x3, Format 06
DataMatrix code

```
[)><RS>06<GS>L[PositionId]<GS>T[PacketId]<GS>1P[ComponentID]<GS>5D[DateOfPrint]<RS><EOT>
```

# TODO:
Seznam věcí, co jsou v plánu a nejsou dokončené:
* Seznam skupin štítků filtrovat dle autora, času, aktuálnosti
* Možnost sdílet jednotlivé skupiny štítků mezi více autory
* Globální odkaz na konkrétní skupiny
* Výběr skupiny do které se budou vkládat nové štítky
* Implementace více typů formátů štítků + pro různé tiskárny
* Forma pro jiné typy štítků než pro sáčky