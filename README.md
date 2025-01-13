# Principles of Programming Languages - Project
## IPPcode20 Parser, Interpreter & Tester
---

Parser, interpreter and tester scripts for the imperative language

**Author:** Peter Koprda <xkoprd00@stud.fit.vutbr.cz>

---

## Overview
This project implements a set of three command-line scripts designed to parse (`parse.php`), interpret (`interpret.py`), and test (`tester.php`) the IPPcode20 imperative language.

### Required Versions:
- **Python**: Version 3.8
- **PHP**: Version 7.4

---

### Parser Script (parse.php)
The `parse.php` script reads source code written in IPPcode20 from the standard input, checks its lexical and syntactical correctness, and outputs an XML representation of the program.

**Usage:**
```
php parse.php < input_file
```

---

### Interpreter Script (interpret.py)
The `interpret.py` script reads an XML representation of an IPPcode20 program, interprets it, and generates the corresponding output. 

**Usage:**
```
python3 interpret.py
```
**Options:**
- `--source=file` - Specifies a file containing the XML representation of the source code.
- `--input=file` - Specifies a file containing input data for the program.

At least one of `--source` or `--input` must be provided. If one of these parameters is missing, the script will attempt to read the data from the standard input.

---

### Test Script (test.php)
The test.php script automates the testing of the parse.php and interpret.py scripts. It scans a given directory (or the current directory by default) for test cases, runs the tests, and generates a comprehensive HTML5 summary of the results.

**Usage:**
```
php test.php
```
**Options:**
- `--directory=path` - Specifies the directory containing the test cases (default is the current directory).
- `--recursive` - Searches for tests recursively in the specified directory and its subdirectories.
- `--parse-script=file` - Specifies the PHP script to be used for parsing (default is `parse.php`).
- `--int-script=file` - Specifies the Python script to be used for interpreting the XML representation (default is `interpret.py`).
- `--parse-only` - Tests only the parser script. It compares the output against reference output files using A7Soft JExamXML.
- `--int-only` - Tests only the interpreter script, with XML input files in `.src` format.
- `--jexamxml=file` - Specifies the location of the JExamXML JAR package used for comparing XML outputs (default is `/pub/courses/ipp/jexamxml/jexamxml.jar`).
