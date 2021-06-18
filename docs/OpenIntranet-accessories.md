## Pomocná zařízení k práci se skladovým systémem

### Čtečka čárových kódů

Pro práci s položkami obsahujícími tištěné štítky používáme běžnou 2D čtečku čárových kódů. Čtečka je připojena k počítači tvořícímu terminál uživatele. 
Při práci se štítky, čtečka usnadňuje identifikaci položek zadáváním kódů do webového formuláře. 

**Podpora čtečky je ve skladovém systému již implementována**

### Čtečka RFID tagů

RFID tagy mají sloužit k označování položek na které se úplně nehodí štítky. Tagy mají oproti štítkům několik potenciálních výhod: 

  * Uložené informace mohou být přepsány a nebo obsahovat dynamické hodnoty (například dobu expirace konkrétní položky, datum vypůjčení položky a informaci o návratu přímo pro uživatele, který s položkou pracuje)
  * RFID tag může usnadnit vyhledávání pložky ve skříni, nebo krabici, neboť lze snadněji zjistit, zda ve vymezeném prostoru je vybraná položka 

**RFID tagy ve skladovém systému zatím implementovány nejsou i když návrh s nimi počítá**

### Skladová váha

Při práci s drobnými položkami, jako jsou například šrouby by se hodil nástroj, kterým by bylo možné odvážit počet odebraných položek. Práce s položkou by vypadala například takto: 

1. Položení zvoleného šuplíku na váhu
2. Načtení štítku položky čtečkou 
3. Ze šuplíku něco odebrat a vrátit jej do skříňky

Počet položek by se v průběhu aktualizoval v databázi.  Zařízení by velmi usnadnilo oddělování konkrétního počtu položek do sáčků pro přepravu, nebo přípravu experimentů. 

Standardním řešením tohoto problému jsou [počítací váhy](https://www.expondo.cz/steinberg-systems-pocitaci-vaha-3-kg-0-05-g-baterie-80-h-10030498)

**Integrace váhy v systému zatím není implementována**

### Organizér s LED podsvětlením 

V dílenských prostorech jsou často používané [závěsné skříňky s průhlednými šuplíky](https://www.svarecky-obchod.cz/dilenske-vybaveni/zavesne-skrinky/15109-zavesna-skrinka-30-m-4-s-2-v-modra-6765m.htm). 
Běžným způsobem organizace položek v těchto šuplících je jejich popsání cedulkami. 

Alternativním řešením je podsvětlení šuplíků ze zadní strany LED osvětlením, které může zvýraznit šuplík se zvolenou položkou. Alternativně elektronika, která zajišťuje podsvětlení může sloužit ke zjištění otevření šuplíčku. Tímto způsobem by mohl být detekován i neautoarizovaný přístup ke skladovým položkám. 

**Funkce asistovaného organizéru zatím ve skladovém systému není implementována, neboť chybí hlavně realizace hardware**






