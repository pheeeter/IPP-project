<!DOCTYPE html>
<html lang = "en-US">
<head>
<meta charset = "UTF-8">
<title>test.php</title>
</head>
<body>
<?php

//=============================================================================================
// Súbor: test.php
// Jazyk: PHP7.4
// Opis: Skript slúži pre automatické testovanie postupnej aplikácie parse.php a interpret.py.
//       Skript prechádza zadaný adresár s testami a využije ich pre automatické otestovanie správnej 
//       funkčnosti parse.php a interpret.py vrátane vygenerovania prehľadného súhrnu v HTML 5 do štandardného výstupu.
// Autor: Peter Koprda (xkoprd00)
//=============================================================================================

/**
 * Návratové kódy programu
 */
define("OK_COMPILATION",0);
define("WRONG_PAR_ERR",10);
define("INPUT_FILE_ERR",11);
define("FILE_OPEN_ERR",12);

/**
 * function check_parameters()
 * 
 * Funkcia na overenie kombinácie zadaných parametrov
 * Ak je skript spustený s parametrom --parse-only, nemôže sa kombinovať s parametrami --int-script a --int-only
 * Ak je skript spustený s parametrom --int-only, nemôže sa kombinovať s parametrami --parse-script a --parse-only
 */
function check_parameters($options){
    if(array_key_exists('parse-only', $options) && (array_key_exists('int-script', $options) || array_key_exists('int-only', $options)) ||
    (array_key_exists('int-only', $options) && array_key_exists('parse-script', $options))){
        fprintf(STDERR, "Zlé parametre!\n");
        exit(WRONG_PAR_ERR);
    }
}

/**
 * function check_files()
 * 
 * Funkcia na zistenie, či existujú súbory interpret.py, parse.php a súbor s JAR balíčkom
 */
function check_files($options, $parser_file, $interpret_file, $jar_file){
    if(!array_key_exists('int-only', $options)){
        if(!file_exists($parser_file)){
            fprintf(STDERR, "Súbor ".$parser_file." neexistuje!\n");
            exit(INPUT_FILE_ERR);
        }
    }
    
    if(!array_key_exists('parse-only', $options)){
        if(!file_exists($interpret_file)){
            fprintf(STDERR, "Súbor ".$interpret_file." neexistuje!\n");
            exit(INPUT_FILE_ERR);
        }
    }
    
    if(!file_exists($jar_file)){
        fprintf(STDERR, "Súbor ".$jar_file." neexistuje!\n");
        exit(INPUT_FILE_ERR);
    }
}

/**
 * function create_files()
 * 
 * Funkcia na vytvorenie chýbajúcich súborov *.in, *.out, *.rc 
 */
function create_files($files_src){
    $file_in_w = $file_out_w = $file_rc_w = [];
    for ($i=0; $i < count($files_src); $i++) {
        $files_arg = substr($files_src[$i], 0, strpos($files_src[$i],'.src'));

        $files_arg_in = $files_arg . ".in";
        if(file_exists($files_arg_in)){
            if(!fopen($files_arg_in, "r")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
        }
        else{
            if(!fopen($files_arg_in, "w")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
        }
        $file_in_w[$i] = $files_arg_in;
        
        $files_arg_out = $files_arg . ".out";
        if(file_exists($files_arg_out)){
            if(!fopen($files_arg_out, "r")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
        }
        else{
            if(!fopen($files_arg_out, "w")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
        }
        $file_out_w[$i] = $files_arg_out;
        
        $files_arg_rc = $files_arg . ".rc";
        if(file_exists($files_arg_rc)){
            if(!fopen($files_arg_rc, "r")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
            $file_rc_w[$i] = $files_arg_rc;
        }
        else{
            $file_rc_w[$i] = $files_arg_rc;
            if(!fopen($file_rc_w[$i], "w")){
                fprintf(STDERR, "Súbor sa nedá otvoriť!\n");
                exit(FILE_OPEN_ERR);
            }
            $fp = fopen($file_rc_w[$i], "w");
            fwrite($fp, "0");
        }
    }
    return array($file_in_w, $file_out_w, $file_rc_w);
}

/**
 * function dir_with_tests()
 * 
 * Funkcia na samotné testovanie skriptov parse.php a interpret.py
 * a na vygenerovanie výstupu do HTML 5
 */
function dir_with_tests($options, $parser_file, $interpret_file, $jar_file){
    $file_in_w = $file_out_w = $file_rc_w = [];
    if(array_key_exists('directory', $options)){
        if(is_dir($options['directory'])){
            if(array_key_exists('recursive', $options)){
                $di = new RecursiveDirectoryIterator($options['directory'], RecursiveDirectoryIterator::SKIP_DOTS);
                $it = new RecursiveIteratorIterator($di);

                $files_src = [];
                foreach($it as $file){
                    if (pathinfo($file, PATHINFO_EXTENSION) == "src"){
                        $file = pathinfo($file, PATHINFO_DIRNAME)."/".pathinfo($file, PATHINFO_BASENAME);
                        array_push($files_src, $file);
                    }  
                }
                list($file_in_w, $file_out_w, $file_rc_w) = create_files($files_src);
            }
            else{
                $files_src = glob($options['directory']."/*.src");
                list($file_in_w, $file_out_w, $file_rc_w) = create_files($files_src);
            }
        }
        else{
            fprintf(STDERR, "Directory ".$options['directory']." does not exist!\n");
            exit(INPUT_FILE_ERR);
        }
    }
    else{
        if(array_key_exists('recursive', $options)){
            $di = new RecursiveDirectoryIterator(getcwd(), RecursiveDirectoryIterator::SKIP_DOTS);
            $it = new RecursiveIteratorIterator($di);

            $files_src = [];
            foreach($it as $file) {
                if (pathinfo($file, PATHINFO_EXTENSION) == "src") {
                    $file = pathinfo($file, PATHINFO_DIRNAME)."/".pathinfo($file, PATHINFO_BASENAME);
                    array_push($files_src, $file);
                }
            }
            list($file_in_w, $file_out_w, $file_rc_w) = create_files($files_src);
            
        }
        else{
            $files_src = glob(getcwd()."/*.src");
            list($file_in_w, $file_out_w, $file_rc_w) = create_files($files_src);
        }
    }

    $all = $passed = $failed = 0;
    print "<style type=\"text/css\">
    .tg  {border-collapse:collapse;border-spacing:0;}
    .tg td{font-family:Arial, sans-serif;font-size:14px;padding:5px 20px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
    .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:5px 15px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
    .tg .tg-cly1{text-align:center;vertical-align:middle}
    .tg .tg-gb0u{background-color:#34ff34;text-align:center;vertical-align:middle}
    .tg .tg-g30i{background-color:#fe0000;text-align:center;vertical-align:middle}
    </style>
    <table class=\"tg\">
    <tr>\n<th class=\"tg-cly1\"><b>Test</b></th>\n<th class=\"tg-cly1\"><b>Status</b></th>\n</tr>\n";
    if(array_key_exists('parse-only', $options)){
        print "<h1>Testing parse.php</h1>";
        for ($i=0; $i < count($files_src); $i++) {
            exec("php ".$parser_file." <".$files_src[$i], $output, $return_code);
            $files_src[$i] = pathinfo($files_src[$i], PATHINFO_FILENAME);
            print "<tr>\n<th class=\"tg-cly1\">".$files_src[$i]."</th>\n";
            if($return_code != 0){
                $fp = fopen($file_rc_w[$i],'r');
                $rc_file = fgets($fp);
                
                
                if($return_code == $rc_file){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
                          
            }
            else{
                fwrite(fopen('output_file','w'),implode("\n",$output));                
                exec("java -jar ".$jar_file." ./output_file ".$file_out_w[$i], $output, $return_code);
                if($return_code == 0){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
                
            }
            print "</tr>\n";
            $output = null;
            $all++;
        }     
    }

    elseif(array_key_exists('int-only', $options)){
        print "<h1>Testing interpret.py</h1>";
        for($i=0; $i < count($files_src); $i++){
            exec("python3 ".$interpret_file." --source=".$files_src[$i]." --input=".$file_in_w[$i], $output, $return_code);
            $files_src[$i] = pathinfo($files_src[$i], PATHINFO_FILENAME);
            print "<tr>\n<th class=\"tg-cly1\">".$files_src[$i]."</th>\n";
            if($return_code != 0){
                $fp = fopen($file_rc_w[$i],'r');
                $rc_file = fgets($fp);
                if($return_code == $rc_file){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
            }
            else{
                exec("echo -n ".join("\n", $output)." > output_file");
                exec("diff output_file ".$file_out_w[$i], $output, $return_status);
                if($return_status == 0){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
                
            }
            print "</tr>\n";
            $output = null;
            $all++;         
        }
    }
    else{
        print "<h1>Testing parse.php and interpret.py</h1>";
        for ($i=0; $i < count($files_src); $i++) {
            exec("php ".$parser_file." <".$files_src[$i], $output, $return_code);
            if($return_code != 0){
                continue;
            }
            fwrite(fopen('output.xml','w'),implode("\n",$output));
            $output = null;
            exec("python3 ".$interpret_file." --source=output.xml --input=".$file_in_w[$i], $output, $return_code);
            $files_src[$i] = pathinfo($files_src[$i], PATHINFO_FILENAME);
            print "<tr>\n<th class=\"tg-cly1\">".$files_src[$i]."</th>\n";
            if($return_code != 0){
                $fp = fopen($file_rc_w[$i],'r');
                $rc_file = fgets($fp);
                if($return_code == $rc_file){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
            }
            else{
                exec("echo -n ".join("\n", $output)." > output_file");
                exec("diff output_file ".$file_out_w[$i], $output, $return_status);
                
                $files_src[$i] = pathinfo($files_src[$i], PATHINFO_FILENAME);
                if($return_status == 0){
                    print "<th class=\"tg-gb0u\">OK</th>\n";
                    $passed++;
                }
                else{
                    print "<th class=\"tg-g30i\">FAILED</th>\n";
                    $failed++;
                }
                
            }
            print "</tr>\n";
            $output = null;
            $all++;
        }
        
        if(file_exists("output.xml")){
            unlink("output.xml");
        }
        
    }

    if(file_exists("output_file")){
        unlink("output_file");
    }

    print "</table>\n
    </section>\n";

    if($all == 0){
        print "<h2>No tests found!</h2>\n";
        return;
    }
    print "<h2>Total tests: ".$all."</h2>\n
    <h2>Passed: ".$passed."</h2>\n
    <h2>Failed: ".$failed."</h2>\n";

    if($failed == 0){
        print "<h2>All tests passed!</h2>\n";
    }
    else{
        print "<h2>Passed test cases percentage: ".(round(($passed/$all)*100,2))."%</h2>\n";
    }

}

/**
 * function help()
 * 
 * Funkcia na vypísanie nápovedy na štandardný výstup
 * Ak je s parametrom --help zadaný iný parameter, program sa ukončí s návratovou hodnotou 10
 */
function help($argv){
    if(count($argv) != 2){
        fprintf(STDERR, "Zlé parametre!\n");
        exit(WRONG_PAR_ERR);
    }
    printf("\nSkript slúži pre automatické testovanie postupnej aplikácie parse.php a interpret.py.
Skript prechádza zadaný adresár s testami a využije ich pre automatické otestovanie správnej
funkčnosti parse.php a interpret.py vrátane vygenerovania prehľadného súhrnu v HTML 5 do štandardného výstupu.\n
Použitie: php7.4 test.php [--help] [--directory=path] [--recursive] [--parse-script=file] [--int-script=file] [--parse-only] [--int-only] [--jexamxml=file]\n
  --help\t\tvypíše túto nápovedu
  --directory=path\ttesty hľadá v zadanom adresári
  --recursive\t\ttesty hľadá nielen v zadanom adresári, ale aj rekurzivne vo všetkých jeho podadresároch
  --parse-script=file\tsúbor so skriptom v PHP 7.4 pre analýzu zdrojového kódu v IPPcode20
  --int-script=file\tsúbor so skriptom v Python 3.8 pre interpret XML reprezentácie kódu v IPPcode20
  --parse-only\t\tbude testovaný iba skript pre analýzu zdrojového kódu v IPPcode20
  --int-only\t\tbude testovaný iba skript pre interpret XML reprezentácie kódu v IPPcode20
  --jexamxml=file\tsúbor s JAR balíčkom s nástrojom A7Soft JExamXML\n\n");
  exit(OK_COMPILATION);
}

/**
 * Hlavná časť programu
 * 
 * Ak je program spustený s parametrom --help (-h), program vypíše nápovedu
 * Program spracúvava zadané parametre pomocou funkcie getopt()
 */
if(isset($argv[1]) && ($argv[1] == "--help" || $argv[1] == "-h")){
    help($argv);
}

$shortopts  = "";
$longopts  = array(

    // Požadovaná hodnota
    "directory::",
    "parse-script::",
    "int-script::",
    "jexamxml::",

    // Žiadna hodnota
    "recursive",       
    "parse-only",
    "int-only",
    "",
);

$options = getopt($shortopts, $longopts);
check_parameters($options);

$parser_file = "parse.php";
$interpret_file = "interpret.py";

# This works only on Merlin
$jar_file = "/pub/courses/ipp/jexamxml/jexamxml.jar";

for ($i=1; $i < count($argv); $i++) { 
    switch(true){
        case preg_match('/^(--directory=[^\n\r=]+)$/m', $argv[$i]):
        case preg_match('/^--recursive$/', $argv[$i]):
        case preg_match('/^--parse-only$/', $argv[$i]):
        case preg_match('/^--int-only$/', $argv[$i]):
            break;
        
        case preg_match('/^--parse-script=[^\n\r=]*parse\.php$/', $argv[$i]):
            $parser_file = substr($argv[$i], strpos($argv[$i], '=')+1);
            break;
        
        case preg_match('/^--int-script=[^\n\r=]*interpret\.py$/', $argv[$i]):
            $interpret_file = substr($argv[$i], strpos($argv[$i], '=')+1);
            break;

        case preg_match('/^--jexamxml=[^\n\r=]*jexamxml\.jar$/', $argv[$i]):
            $jar_file = substr($argv[$i], strpos($argv[$i], '=')+1);
            break;

        default:
            fprintf(STDERR, "Zlé parametre!\n");
            exit(WRONG_PAR_ERR);
    }
}


check_files($options, $parser_file, $interpret_file, $jar_file);
dir_with_tests($options, $parser_file, $interpret_file, $jar_file);

?>
</body>
</html>

