## Implementačná dokumentácia k 2. úlohe do IPP 2019/2020
### Meno a priezvisko: Peter Koprda
### Login: xkoprd00
***
## **Skript interpret&#46;py**
Skript načíta XML reprezentáciu programu pomocou parametra **--source=file** a s využitím štandardného vstupu alebo pomocou parametra **--input=file** tento program interpretuje a generuje výstup.

### **Spracovanie parametrov príkazového riadka**
Na spracovanie parametrov príkazového riadka bola použitá knižnica *argparse*. Okrem parametrov **--source=file** a **--input=file** môže byť zadaný parameter **--help**, ktorý na štandardný výstup vypíše nápovedu interpretu a ukončí sa s návratovou hodnotou 0. Tento parameter musí byť zadaný samostatne, inak sa skript ukončí s návratovou hodnotou 10.

### **Analýza načítaného XML**
Na načítanie vstupného XML bola použitá knižnica *xml&#46;etree&#46;ElementTree*. Vstupné XML sa spracováva vo funkcii *sourceXML()*, ktorá obsahuje vstupný parameter - *súbor s XML* a vracia koreňový element XML - *root*. Jednotlivé inštrukcie sa najprv zoradia podľa poradia čísla *order*  a následne sa zoradia argumenty takisto podľa poradia v každej inštrukcii.\
 Každá inštrukcia obsahuje element *opcode*, ktorý obsahuje operačný kód. Tento operačný kód sa spracováva vo funkcii *checkOpcode* a analyzuje sa, či argumenty tejto inštrukcie nemajú lexikálnu alebo syntaktickú chybu, ktorá chyba vedie k ukončenie programu s návratovou hodnotou 32.

### **Interpretácia XML a generovanie výstupu**
Samotná interpretácia XML prebieha v triede *Interpretation*, ktorá obsahuje metódy podľa názvu operačných kódov. Každý operačný kód má vlastnú metódu, v ktorej sa interpretuje inštrukcia podľa názvu operačného kódu. Na dátový zásobník sú konštanty ukladané bez dátových typov.

### **Bonusové rozšírenia FLOAT a STACK**
Rozšírenie **FLOAT** podporuje inštrukcie *FLOAT2INT*, *INT2FLOAT*,zásobníkovú inštrukciu *POPS* (v ktorej prebieha vyhodnotenie typu konštanty), aritmetické inštrukcie *ADD*, *SUB*, *MUL* a *DIV*.\
Rozšírenie **STACK** podporuje inštrukcie viacero zásobníkových inštrukcií, ale nie je možné overiť, či sú dané inštrukcie rovnakého typu.

***
## **Skript test&#46;php**
Skript slúži na automatické testovanie skriptov *parse&#46;php* a *interpret&#46;py*.

### **Spracovanie parametrov príkazového riadka**
Na spracovanie parametrov príkazového riadka bola použitá funkcia *getopt*. Na vypísanie nápovedy na štandardný výstup musí byť skript spustený s parametrom *--help*. Ak bol zadaný parameter *--parse-only*, testovaný bol iba skript *parse&#46;php*, ak bol zadaný parameter *--int-only*, testovaný bol iba skript *interpret&#46;py*, inak skript testuje skripty *parse&#46;php* a *interpret&#46;py*.

### **Testovanie skriptov**
Po spustení skriptu sa overí pomocou funkcie *check_files()*, či existujú testované skripty a či existuje súbor s JAR baličkom s nástrojom A7Soft JExamXML. Ak aspoň jeden súbor neexistuje, tak potom sa program ukončí s návratovou hodnotou 11. Samotné testovanie skriptov prebieha vo funkcii *dir_with_tests()*, v ktorej sa nachádzajú podmienky, ktoré sa vykonávajú podľa parametrov príkazového riadka.

### **Generovanie výsledkov testov**
Výsledky o úspešnosti/neúspešnosti jednotlivých testov sú vygenerované do HTML verzie 5. Nadpis uvádza, či sa testuje skript *parse&#46;php*, *interpret&#46;py* alebo obidva skripty. Nasleduje tabuľka s názvami a výsledkami testov, v každom riadku sa nachádza jeden test a výsledok tohto testu - ak je test úspešný, vypíše sa do bunky **OK**, ak nie, vypíše sa **FAILED**. Na konci tejto vygenerovanej stránky je vypísaný počet testov, počet úspešných testov, počet neúspešných testov a percento úspešnosti testov.
