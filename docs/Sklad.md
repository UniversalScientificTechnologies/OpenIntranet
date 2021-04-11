# Modul ```sklad```

Modul sklad slouží pro agendu ohledně správy skladu a skladových zásob. 

Nejmenší skladová entita je sáček. 

## Schopnosti
 * Vytvářet skladové položky
 * Duplikovat skladové položky
 * Přehled všech skladových zásob
 * Rozdělování na sáčky


## Access rights
 | Označení | Název | Popis | 
 |----------|-------|-------|
 | ```stock-sudo``` | Správce skladu | Kompletní přístup ke všem funkcím skladu. Včetně možnosti pokročilé editace |
 | ```stock-manager``` | Manažer skladu | Stará se o chod skladu, může vytvářet nové součástky, provádět všechny skladové operace včetně nákupu a podobných záležitostí. |
| ```stock-user``` | Uživatel skladu | Uživatel může pouze prohlížet sklad a dělat některé operace. Například servisní odběr. Uživatel nevidí některé citlivé údaje. Jako dodavatel nebo ceny nákupů. Má přístup ke skladovým počtům.| 
| ```stock-guest``` | Návštěvník skladu | Nemůže provádět žádné skladové operace. Pouze přístup k necitlivým údajům.|


