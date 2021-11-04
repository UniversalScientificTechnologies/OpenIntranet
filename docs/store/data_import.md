---
layout: default
title: External data sources
parent: Store - Warehouse management system
nav_order: 4
---

# Store data import

Mnoho dodavatelů komponent nabízí velmi rozsáhlá API pro získání stavu objednávek, pro tvorbu objednávek nebo jen pro získání dalších informací o produktech. Data import se stará o správu připojení k jednotlivým dodavatelským API


### TME.eu

TME je významný dodavatel elektronických součástek. 


#### Konfigurace 
Pro rozfungování získávání údajů je nutné zaregistrovat aplikaci v jejich vývojářském rozhraní. Na základě této registrace se získají dva kódy. Tzv. `Token` a `Application secret` kód. 

Na stránce developers.tme.eu se přihlásíme přistupem uživatelským účtem z TME. Otevřeme záložku API keys, kde vyplníme název Aplikace (v našem případě třeba OpenIntranet) a klikneme vygenerovat nový klíč. 
![obrazek](https://user-images.githubusercontent.com/5196729/140304413-ed072970-b7ba-49c2-bcc5-c64ce5408c9a.png)

Po odkliknutí se v seznamu zobrazí naše aplikace. S kódy 'Anonymous key' a 'Application secret'. 
![obrazek](https://user-images.githubusercontent.com/5196729/140304750-25e7ac96-dd08-49c7-84a6-2e8dff5602be.png)

Tyto ůdaje je následně potřeba předat OpenIntranetu. To lze udělat GET požadavkem. Ve webovém prohlížeči otevřeme intranet, přihlásíme se tam. 

Následně přejdeme na adresu:
```
  https://<url_open_intranet>/store/data_import/tme/registr?token=<Anonymous key>&app_secret=<Application secret>
```
_Klíče musíte dosadit vlastní, které jsme získali v předchozích krocích_

Tím si OpenIntranet uloží tyto klíče a toto uložení vám v prohlížeči potvrdí. 

Na adrese:
```
  https://<url_open_intranet>/store/data_import/tme/registr
```
pak obdržíme tzv. Nonce kód, který je nutné zaregistrovat ve vlastním TME Účtu. 
Přihlásíme se tedy na stránce tme.eu a přejdeme do `Panel uživatele` -> `Aplikace`

![obrazek](https://user-images.githubusercontent.com/5196729/140308111-d7f25ac2-5bc0-4457-b90a-a96547fd2137.png)

Klikneme na 'Register new app'

![obrazek](https://user-images.githubusercontent.com/5196729/140308217-f6d4b572-5871-47b0-829c-31ded206cb33.png)

A do pole vložime získaný 'Nonce' klíč:

![obrazek](https://user-images.githubusercontent.com/5196729/140308289-a3165a67-f278-4b7f-9a7d-64fd04baa5c6.png)

V dalším kroku získáme kód, token, který znovu vložíme do OpenIntranetu. 

![obrazek](https://user-images.githubusercontent.com/5196729/140308406-fde556a0-d59e-42c6-bcef-b53baab4d73d.png)







