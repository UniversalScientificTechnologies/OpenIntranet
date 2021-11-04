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
