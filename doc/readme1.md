## Implementačná dokumentácia k 1. úlohe do IPP 2019/2020
### Meno a priezvisko: Peter Koprda
### Login: xkoprd00
***
## Analýza zdrojového kódu IPPcode20
Zdrojový kód je čítaný po riadkoch zo štandardného vstupu. Najprv sa skontroluje, či sa v zdrojovom kóde nachádza hlavička **.IPPcode20** pomocou funkcie *header_check()*, pričom je možných výskyt prázdnych riadkov alebo riadkov s komentármi pred touto hlavičkou. Potom sa pomocou funkcie *code_check()* kontroluje lexikálne a syntaktické pravidlá jazyka IPPcode20. U každej inštrukcie sa kontroluje pomocou regulárnych výrazov počet a typy operandov (premenná, konštanta, návestie, typ).

Pre generovanie XML reprezentácie zdrojového kódu IPPcode20 bol použitý nástroj **XMLWriter**.

***
## Spracovanie parametrov príkazového riadka
Spracovávanie parametrov príkazového riadka je implementované v hlavnej časti programu. Ak je zadaný parameter *--help*, zavolá sa funkcia *help()*, skontroluje sa, či je tento parameter zadaný samostatne, ak áno, vypíše sa nápoveda ku skriptu a ak nie, skript sa ukončí s návratovým kódom 10.

***
## Implementované rozšírenie
V rámci úlohy 1 bolo naimplementované rozšírenie pre zbieranie štatistík - **STATP**

Keď je so skriptom *parse.php* zadaný parameter **--stats=file**, tak sú behom lexikálnej a syntaktickej analýzy zbierané štatistiky o spracovanom zdrojovom kóde. Na konci analýzy sú spracované štatistiky uložené do zadaného súboru *file* v takom poradí, v akom boli zadané na príkazovom riadku.

Pre každú zaznamenávanú hodnotu je vytvorený číselný sčítač, ktorý sa v priebehu analýzy navyšuje. Pri zadaní parametru **--loc** sa počíta počet riadkov s inštrukciami. Pri zadaní parametru **--comments** sa počíta počet riadkov na ktorých sa vyskytoval komentár. Pri zadaní parametru **--labels** sa počíta počet definovaných návestí. Pri zadaní parametru **--jumps** sa počíta počet inštrukcií pre podmienené/nepodmienené skoky, volania a návraty z volania dohromady (t.j. inštrukcie *JUMP*, *JUMPIFEQ*, *JUMPIFNEQ*, *CALL* a *RETURN*).

Ak s parametrom **--stats=file** nie je zadaný žiadny iný parameter, vytvorí sa súbor *file*, ale nič sa do neho nevypíše. Ale ak sú zadané nejaké upresňujúce parametry, ale nie je zadaný parameter **--stats=file**, tak sa ukončí s návratovým kódom 10.