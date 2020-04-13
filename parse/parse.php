<?php

//=============================================================================================
// Súbor: parse.php
// Jazyk: PHP7.4
// Opis: Skript typu filter načíta zo štandardného vstupu zdrojový kód v IPPcode20,
//       skontroluje lexikálnu a syntaktickú správnosť kódu a vypíše na štandardný výstup XML reprezentáciu programu.
// Autor: Peter Koprda (xkoprd00)
//=============================================================================================


/**
 * Návratové kódy programu
 */
define("OK_COMPILATION",0);
define("WRONG_PAR_ERR",10);
define("FILE_OPEN_ERR",12);
define("WRONG_HEADER_ERR",21);
define("WRONG_OPCODE_ERR",22);
define("LEX_SYNTAX_ERR",23);

/** 
 * function header_check()
 * 
 * Funkcia na overenie, či sa v zdrojom kóde nachádza hlavička .IPPcode20
 * Ak sa hlavička nenáchadza, program sa ukončí s chybou 21
 */
function header_check(){
    do{
        $line = trim(fgets(STDIN));
        if(preg_match('/(\.ippcode20)\s*(#[^\r\n]*)/', strtolower($line)) || feof(STDIN)){
            break;
        }
    } while(preg_match('/#[^\r\n]*/', $line) || preg_match('/^\s*$/', $line));
    
    if(!preg_match('/^((\.ippcode20)\s*(#+.*))$|^(\.ippcode20)$/m', strtolower($line))){
        fprintf(STDERR,"Chybná hlavička!\n");
        exit(WRONG_HEADER_ERR);
    }
    #fprintf(STDOUT,"HEY\n");
    
}

/**
 * function variable_check($instruction)
 * 
 * Funkcia na skontrolovanie mena premennej
 * Ak je meno premennej nesprávne, ukončí sa program s chybou 23
 * Ak je meno premennej správne, vráti sa typ "var" na výpis do XML
 */
function variable_check($instruction){
    if(!preg_match('/^(GF|LF|TF)@([A-Za-z_\-\$&%*!?])([A-Za-z\d_\-\$&%*!?]*)$/m', $instruction)){
        fprintf(STDERR,"Chybný operand!\n");
        exit(LEX_SYNTAX_ERR);
    }
    return "var";
}

/**
 * function constant_check($instruction)
 * 
 * Funkcia na skontrolovanie konštanty alebo mena premennej
 * Ak je meno premennej alebo konštanty nesprávne, ukončí sa program s chybou 23
 * Ak je to premenná, vráti sa typ "var" na výpis do XML
 * Ak je to konštanta, vráti sa typ konštanty (int|bool|nil|string) spolu s hodnotou konštanty na výpis do XML
 */
function constant_check($instruction){
    if(!preg_match('/(^(GF|LF|TF)@([A-Za-z_\-\$&%*!?])([A-Za-z\d_\-\$&%*!?]*)$)|^(int@[-+]?\d+)$|^(bool@(true|false))$|^(nil@nil)$|^(string@([^\n\r\\\\\s#]*(\\\\[0-9]{3})?[^\n\r\\\\\s#]*)*)$/m', $instruction)){
        fprintf(STDERR,"Chybný operand!\n");
        exit(LEX_SYNTAX_ERR);
    }

    elseif(preg_match('/^(GF|LF|TF)@([A-Za-z_\-\$&%*!?])([A-Za-z\d_\-\$&%*!?]*)$/', $instruction)){
        return "var";
    }
    $const = explode('@', $instruction, 2);
    return $const;
}

/**
 * function label_check($instruction)
 * 
 * Funkcia na skontrolovanie mena návestia
 * Ak je meno návestia nesprávne, ukončí sa program s chybou 23
 * Ak je meno návestia správne, vráti sa typ "label" na výpis do XML
 */
function label_check($instruction){
    if(!preg_match('/^([A-Za-z_\-\$&%*!?])([A-Za-z\d_\-\$&%*!?]*)$/', $instruction)){
        fprintf(STDERR,"Chybný operand!\n");
        exit(LEX_SYNTAX_ERR);
    }
    return "label";
}

/**
 * function type_check($instruction)
 * 
 * Funkcia na skontrolovanie datového typu (int, string, bool)
 * Ak je datový typ nesprávny, ukončí sa program s chybou 23
 * Ak je datový typ správny, vráti sa typ "type" na výpis do XML
 */
function type_check($instruction){
    if(!preg_match('/^(int|string|bool)$/', $instruction)){
        fprintf(STDERR,"Chybný operand!\n");
        exit(LEX_SYNTAX_ERR);
    }
    return "type";
}

/**
 * function overflow_of_operands($instruction)
 * function underflow_of_operands($instruction)
 * 
 * Funkcie na skontrolovanie počtu operandov operačného kódu
 * Ak je počet parametrov nesprávny, program sa ukončí s chybou 23
 */
function overflow_of_operands($instruction){
    if(!preg_match('/^#[^\r\n]*$/', $instruction)){
        fprintf(STDERR,"Chybný počet operandov!\n");
        exit(LEX_SYNTAX_ERR);
    }
}

function underflow_of_operands($instruction, $count){
    if(count($instruction) < $count){
        fprintf(STDERR,"Chybný počet operandov!\n");
        exit(LEX_SYNTAX_ERR);
    }
}

/**
 * function write_special_chars_xml($xw, $type)
 * 
 * Pomocná funkcia na vypísanie špeciálnych znakov
 */
function write_special_chars_xml($xw, $type, $i){
    $j = 0;
    while(isset($type[$i][1][$j])){
        switch ($type[$i][1][$j]) {
            case '<':
                xmlwriter_write_raw($xw, "&lt;");
                break;

            case '&':
                xmlwriter_write_raw($xw, "&amp;");
                break;

            case '>':
                xmlwriter_write_raw($xw, "&gt;");
                break;

            case '"':
                xmlwriter_write_raw($xw, "&quot;");
                break;

            case '\'':
                xmlwriter_write_raw($xw, "&apos;");
                break;
            
            default:
                xmlwriter_write_raw($xw, $type[$i][1][$j]);
                break;
        }
        $j++;
    } 
}


/**
 * function write_xml($xw, $order, $instruction, $type)
 * 
 * Funkcia na vypísanie XML reprezentácie programu na štandardný výstup
 * Cyklus for slúži na vypísanie operandov operačného kódu
 */
function write_xml($xw, $order, $instruction, $type){
    xmlwriter_start_element($xw, 'instruction');
    xmlwriter_write_attribute($xw, 'order', $order);
    xmlwriter_write_attribute($xw, 'opcode', strtoupper($instruction[0]));
    $tmp = "arg";

    for($i=1; $i < count($instruction) ; $i++){ 
        $arg = $tmp . $i;
        xmlwriter_start_element($xw, $arg);
        if(isset($type[$i])){
            if($type[$i] == 'var' || $type[$i] == 'label' || $type[$i] == 'type'){
                xmlwriter_write_attribute($xw, "type", $type[$i]);
                xmlwriter_text($xw, $instruction[$i]);
            }
            else{
                xmlwriter_write_attribute($xw, "type", $type[$i][0]);
                if($type[$i][1] != ''){
                    if(!preg_match('/\'/', $type[$i][1])){
                        xmlwriter_text($xw, $type[$i][1]);
                    }
                    else{
                        write_special_chars_xml($xw, $type, $i);
                    }
                    
                }
            }
        }
        xmlwriter_end_element($xw);
    }
    xmlwriter_end_element($xw);
}

/**
 * function code_check($order)
 * 
 * Funkcia na overenie lexiky a syntaxe inštrukcií
 * Funkcia číta vstup riadok po riadku a kontroluje lexiku operačných kódov pomocou switch case
 * a následne funkcia kontroluje syntax operačných kódov t.j. kontroluje počet operandov
 * 
 */
function code_check($order){
    $loc = $comments = $labels = $jumps = 0;

    $xw = xmlwriter_open_memory();
    xmlwriter_set_indent($xw, 2);
    $res = xmlwriter_set_indent_string($xw, '  ');
    
    xmlwriter_start_document($xw, '1.0', 'UTF-8');
    xmlwriter_start_element($xw, 'program');
    xmlwriter_start_attribute($xw, 'language');
    xmlwriter_text($xw, 'IPPcode20');
    xmlwriter_end_attribute($xw);

    do{
        $line = trim(fgets(STDIN));
        if(preg_match('/^#[^\r\n]*$/m', $line)){
            $comments++;
            continue;    
        }
        elseif($line == NULL){
            continue;
        }

        if(strpos($line,'#') != false){
            $line = substr($line, 0, strpos($line,'#'));
            $comments++;
        }
        $instruction = preg_split('/\s+/', trim($line));
        $operands = 2;
        $type = NULL;
        $loc++;

        switch(strtolower($instruction[0])){

            ### Rámce, volania funkcií
            case "move":
                if(count($instruction) < 3){
                    fprintf(STDERR,"Chybný počet operandov!\n");
                    exit(LEX_SYNTAX_ERR);
                }
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $operands = 3;
                break;
            
            case "createframe":
            case "pushframe":
            case "popframe":
                $operands = 1;
                break;

            case "return":
                $operands = 1;
                $jumps++;
                break;

            case "defvar":
                underflow_of_operands($instruction, 2);
                $type[1] = variable_check($instruction[1]);
                break;

            case "call":
                underflow_of_operands($instruction, 2);
                $type[1] = label_check($instruction[1]);
                $jumps++;
                break;

            # Dátové zásobníky
            case "pushs":
                underflow_of_operands($instruction, 2);
                $type[1] = constant_check($instruction[1]);
                break;
                
            case "pops":
                underflow_of_operands($instruction, 2);
                $type[1] = variable_check($instruction[1]);
                break;

            # Aritmetické, relačné, booleovské a konverzné inštrukcie
            case "add":
            case "sub":
            case "mul":
            case "idiv":
            case "lt":
            case "gt":
            case "eq":
            case "and":
            case "or":
                underflow_of_operands($instruction, 4);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $type[3] = constant_check($instruction[3]);
                $operands = 4;
                break;

            case "not":
                underflow_of_operands($instruction, 3);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $operands = 3;
                break;
            
            case "int2char":
                underflow_of_operands($instruction, 3);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $operands = 3;
                break;

            case "stri2int":
                underflow_of_operands($instruction, 4);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $type[3] = constant_check($instruction[3]);
                $operands = 4;
                break;

            # Vstupno-výstupné inštrukcie
            case "read":
                underflow_of_operands($instruction, 3);
                $type[1] = variable_check($instruction[1]);
                $type[2] = type_check($instruction[2]);
                $operands = 3;
                break;

            case "write":
                underflow_of_operands($instruction, 2);
                $type[1] = constant_check($instruction[1]);
                break;

            # Reťazce
            case "concat":
            case "getchar":
            case "setchar":
                underflow_of_operands($instruction, 4);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $type[3] = constant_check($instruction[3]);
                $operands = 4;
                break;

            case "strlen":
                underflow_of_operands($instruction, 3);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $operands = 3;
                break;

            # Typy
            case "type":
                underflow_of_operands($instruction, 3);
                $type[1] = variable_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $operands = 3;
                break;

            # Riadenie toku programu
            case "label":
                underflow_of_operands($instruction, 2);
                $type[1] = label_check($instruction[1]);
                $labels++;
                break;

            case "jump":
                underflow_of_operands($instruction, 2);
                $type[1] = label_check($instruction[1]);
                $jumps++;
                break;

            case "jumpifeq":
            case "jumpifneq":
                underflow_of_operands($instruction, 4);
                $type[1] = label_check($instruction[1]);
                $type[2] = constant_check($instruction[2]);
                $type[3] = constant_check($instruction[3]);
                $operands = 4;
                $jumps++;
                break;

            case "exit":
                underflow_of_operands($instruction, 2);
                $type[1] = constant_check($instruction[1]);
                break;

            # Ladiace inštrukcie
            case "dprint":
                underflow_of_operands($instruction, 2);
                $type[1] = constant_check($instruction[1]);
                break;

            case "break":
                $operands = 1;
                break;

            # Chybný operačný kód
            default:
                fprintf(STDERR,"Chybný operačný kód!\n");
                exit(WRONG_OPCODE_ERR);
        }

        if(array_key_exists($operands,$instruction)){
            overflow_of_operands($instruction[$operands]);
        }
        write_xml($xw, ++$order, $instruction, $type);
        
    } while(!feof(STDIN));

    xmlwriter_end_element($xw); 
    xmlwriter_end_document($xw);
    echo xmlwriter_output_memory($xw);

    $statistics = array($loc, $comments, $labels, $jumps);
    return $statistics;
}

/**
 * function help($argv)
 * 
 * Funkcia na výpis nápovedy na štandardný výstup a program sa ukončí s návratovým kódom 0
 * Ak je s parametrom --help zadaný ešte iný parameter, program sa ukončí s návratovým kódom 10
 */
function help($argv){
    if(count($argv) != 2){
        fprintf(STDERR,"Zlé parametre\n");
        exit(WRONG_PAR_ERR);
    }
    printf("\nSkript typu filter (parse.php v jazyku PHP 7.4) načíta zo štandardného vstupu zdrojový kód v IPPcode20,
skontroluje lexikálnu a syntaktickú správnosť kódu a vypíše na štandardný výstup XML reprezentáciu programu podľa špecifikácie.\n
Použitie: php7.4 parse.php [--help] [--stats=file] [--loc] [--comments] [--labels] [--jumps]\n
  --help\tvypíše túto nápovedu
  --stats=file\tvypíše štatistiky do súboru
  --loc\t\tvypíše do štatistík počet riadkov s inštrukciami
  --comments\tvypíše do štatistík počet riadkov na ktorých sa vyskytoval komentár
  --labels\tvypíše do štatistík počet definovaných návestí
  --jumps\tvypíše do štatistík počet inštrukcií pre podmienené/nepodmienené skoky, volania a návraty z volania dohromady\n\n");
    exit(OK_COMPILATION);
}

/**
 * Hlavná časť programu
 * 
 * Ak je program spustený s parametrom --help (-h), vypíše sa nápoveda
 * V else sa nachádza naimplementované rozšírenie STATP,
 * ktoré vypisuje štatistiku zdrojového kódu do súboru (parametre zadáva užívateľ)
 * Ak nie sú zadané žiadne parametre, program nevytvára štatistiku
 */
if(count($argv) == 2 && ($argv[1] == "--help" || $argv[1] == "-h")){
    help($argv);
}  
else{
    $count_arg_stats = 0;
    $stats = false;
    for($i=1; $i < count($argv); $i++){ 
        if(preg_match('/^(--stats=[^\n\r]*)$/m',$argv[$i])){
            if(preg_match('/--stats=([^\n\r]*=+[^\n\r]*)/', $argv[$i]) || $argv[$i] == "--stats="){
                fprintf(STDERR, "Zlé parametre!\n");
                exit(WRONG_PAR_ERR);
            }
            $count_arg_stats++;
            if($count_arg_stats == 1) {
                $tmp = $argv[$i];
            }
        }
    }
    if($count_arg_stats != 1 && count($argv) != 1){
        fprintf(STDERR, "Zlé parametre!\n");
        exit(WRONG_PAR_ERR);
    }
    elseif($count_arg_stats == 1){
        $stats = explode('=', $tmp);
        header_check();
        $statistics = code_check($order=0);
        $file = fopen($stats[1], "w");
        if(!$file){
            fprintf(STDERR, "Nemožno otvoriť súbor!\n");
            exit(FILE_OPEN_ERR);
        }
        $stats_exist = false;
        for ($i=1; $i < count($argv); $i++) {
            if(preg_match('/^(--stats=[^\n\r]*)$/m',$argv[$i])){
                $stats_exist = true;
                continue;
            }
            switch ($argv[$i]) {
                case "--loc":
                    fwrite($file, $statistics[0]."\n");
                    break;
                
                case "--comments":
                    fwrite($file, $statistics[1]."\n");
                    break;
                
                case "--labels":
                    fwrite($file, $statistics[2]."\n");
                    break;

                case "--jumps":
                    fwrite($file, $statistics[3]."\n");
                    break;

                default:
                    fprintf(STDERR, "Zlé parametre!\n");
                    exit(WRONG_PAR_ERR);
            }
        }
        if($stats_exist = false){
            fprintf(STDERR, "Zlé parametre!\n");
            exit(WRONG_PAR_ERR);
        }
        fclose($file);
    }
    else{
        header_check();
        code_check($order=0);
    }
    exit(OK_COMPILATION);
}

?>