#!/usr/bin/python3

# =============================================================================================
# Súbor: interpret.py
# Jazyk: Python 3.8
# Opis: Program načíta XML reprezentáciu programu a tento program s využitím vstupu
#       podľa parametrov príkazového riadka interpretuje a generuje výstup.
# Autor: Peter Koprda (xkoprd00)
# =============================================================================================

import argparse
import re
import sys
import xml.etree.ElementTree as ElementTree

label_frame = []


# Triedy na vyhadzovanie chybových hlášok a ukončenie programu s určitým návratovým kódom."""


class ParameterException(Exception):
    pass


class FileInputException(Exception):
    pass


class XMLFormatException(Exception):
    pass


class XMLStructureException(Exception):
    pass


class SemanticException(Exception):
    pass


class OperandTypeException(Exception):
    pass


class UndeclaredVariableException(Exception):
    pass


class UndeclaredFrameException(Exception):
    pass


class MissingValueException(Exception):
    pass


class ValueOperandException(Exception):
    pass


class StringOperationException(Exception):
    pass


class Interpretation:
    """
    Trieda, ktorá interpretuje zdrojový súbor.

    Na začiatku prebehne inicializácia triedy.
    Každý operačný kód sa spracováva samostatne, využíva pri tom metódu switch().
    """

    def __init__(self, global_frame, gf_ind, local_frame, lf_ind, temporary_frame,
                 call_stack, data_stack):
        """
        Parametre
        ----------
        global_frame : list v liste
            Globálny rámec, ktorý slúži na ukladanie globálnych premenných
        gf_ind : int
            Umiestnenie indexu v globálnom rámci
        local_frame : list v liste
            Lokálny rámec, ktorý slúži na ukladanie lokálnych premenných
        lf_ind : int
            Umiestnenie indexu v lokálnom rámci
        temporary_frame : list
            Dočasný rámec, ktorý slúži na ukladanie dočasných premenných
        call_stack : list
            Zásobník, ktorý slúži na volanie funkcií
        data_stack : list
            Dátový zásobník
        """
        self.global_frame = global_frame
        self.local_frame = local_frame
        self.temporary_frame = temporary_frame
        self.label_frame = label_frame
        self.gf_ind = gf_ind
        self.lf_ind = lf_ind
        self.call_stack = call_stack
        self.data_stack = data_stack

    def switch(self, opcode, root, i):
        """
        Metóda pre zmenenie metódy podľa názvu operačného kódu
        """
        return getattr(self, opcode)()

    def MOVE(self):
        """ Skopíruje hodnotu <symb> do <var>
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])

        if type_symb[1] == "string":
            text[1] = stringConversion(text[1])

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, text[1],
                                                                                 type_symb[1])

    def CREATEFRAME(self):
        """ Vytvorí nový dočasný rámec
        """
        self.temporary_frame = []

    def PUSHFRAME(self):
        """ Presunie TF na zásobník rámcov
        """
        if self.temporary_frame is None:
            raise UndeclaredFrameException
        elif self.local_frame is None:
            self.local_frame = []
        if self.temporary_frame:
            self.local_frame.append(self.temporary_frame)
        self.temporary_frame = None

    def POPFRAME(self):
        """ Presunie vrcholový rámec LF zo zásobníka rámcov do TF
        """
        if self.local_frame is None:
            raise UndeclaredFrameException
        if self.temporary_frame is None or self.temporary_frame == []:
            self.temporary_frame = []
        else:
            self.temporary_frame.pop()
        self.temporary_frame.append(self.local_frame.pop())

    def DEFVAR(self):
        """ Definuje premennú v určenom rámci
        """
        type_symb, text = argumentsXML(root, i)
        frame = ''.join(text)[:2]
        variable = ''.join(text)[3:]

        if frame == "GF":
            self.global_frame.append([])
            self.global_frame[self.gf_ind].append(variable)
            for y in self.global_frame:
                if self.global_frame.count(y) > 1:
                    raise SemanticException
            self.gf_ind += 1
        elif frame == "LF":
            if self.local_frame is None:
                raise UndeclaredFrameException
            self.local_frame.append([])
            self.local_frame[self.lf_ind].append(variable)
            for y in self.local_frame:
                if self.local_frame.count(y) > 1:
                    raise SemanticException
            self.lf_ind += 1
        else:
            if self.temporary_frame is None:
                raise UndeclaredFrameException
            self.temporary_frame.append(variable)

    def CALL(self):
        """ Uloží inkrementovanú aktuálnu pozíciu z interného čítača inštrukcií
        do zásobníka volania a vykoná skok na zadané návestie
        """
        label_symb = labels()
        self.call_stack.append(i)
        index = jumpToLabel(label_symb)
        return index

    def RETURN(self):
        """ Vyjme pozíciu zo zásobníka volania a skočí na túto pozíciu nastavením interného čítača inštrukcií
        """
        if not self.call_stack:
            raise MissingValueException
        position = self.call_stack.pop()
        return position + 1

    def PUSHS(self):
        """ Uloží hodnotu na dátový zásobník
        """
        type_symb, text = argumentsXML(root, i)
        frame = ''.join(text)[:2]
        value = ''.join(text)[3:]

        if type_symb == "var" and frame == "GF":
            try:
                symb = self.global_frame.index(value)
            except Exception:
                raise UndeclaredVariableException
        elif type_symb == "var" and frame == "LF":
            try:
                symb = ''.join(self.local_frame.pop())
                if symb != value:
                    raise UndeclaredVariableException
                self.local_frame.append(symb)
            except Exception:
                raise UndeclaredVariableException
        elif type_symb == "var" and frame == "TF":
            try:
                symb = self.temporary_frame.index(value)
            except Exception:
                raise UndeclaredVariableException
        else:
            symb = ''.join(text)
        self.data_stack.append(symb)

    def POPS(self):
        """ Vyjme zo zásobníka hodnotu a uloží ju do premennej
        Ak je zásobník prázdny, dôjde k chybe 56
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        try:
            value = self.data_stack.pop()
        except Exception:
            raise MissingValueException

        if re.match('^([-+]?\d+)$', str(value)):
            value_type = "int"
        elif re.match('^(true|false)$', str(value)):
            value_type = "bool"
        elif value == "nil":
            value_type = "nil"
        elif re.match('^(([-+]?0x[0-9]\.?[0-9a-f]*p[+-][0-9]*)|(0x[0-9]\.[0-9]+)|([-+]?\.?[0-9]+))$', value):
            # Rozšírenie FLOAT
            value_type = "float"
        else:
            value_type = "string"
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, value,
                                                                                 value_type)

    """ ---------------- Rozšírenie STACK ---------------- """

    def CLEARS(self):
        self.data_stack = []

    def ADDS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            result = int(symb1) + int(symb2)
        except Exception:
            raise OperandTypeException
        self.data_stack.append(result)

    def SUBS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            result = int(symb1) - int(symb2)
        except Exception:
            raise OperandTypeException
        self.data_stack.append(result)

    def MULS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            result = int(symb1) * int(symb2)
        except Exception:
            raise OperandTypeException
        self.data_stack.append(result)

    def IDIVS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            result = int(symb1) // int(symb2)
        except Exception:
            raise ValueOperandException
        self.data_stack.append(result)

    def LTS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if (symb1 == "nil" and symb2 != "nil") or \
                (symb1 != "nil" and symb2 == "nil"):
            raise OperandTypeException
        elif type(symb2) != type(symb1):
            raise OperandTypeException
        result = (str(symb1 < symb2)).lower()
        self.data_stack.append(result)

    def GTS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if (symb1 == "nil" and symb2 != "nil") or \
                (symb1 != "nil" and symb2 == "nil"):
            raise OperandTypeException
        elif type(symb2) != type(symb1):
            raise OperandTypeException
        result = (str(symb1 > symb2)).lower()
        self.data_stack.append(result)

    def EQS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if type(symb2) != type(symb1):
            raise OperandTypeException
        result = (str(symb1 == symb2)).lower()
        self.data_stack.append(result)

    def ANDS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if (symb1 != "true" and symb1 != "false") or \
                (symb1 != "true" and symb1 != "false"):
            raise OperandTypeException
        elif symb1 == "true" and symb2 == "true":
            result = "true"
        else:
            result = "false"
        self.data_stack.append(result)

    def ORS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if (symb1 != "true" and symb1 != "false") or \
                (symb1 != "true" and symb1 != "false"):
            raise OperandTypeException
        elif symb1 == "true" or symb2 == "true":
            result = "true"
        else:
            result = "false"
        self.data_stack.append(result)

    def NOTS(self):
        try:
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if symb1 == "true":
            result = "false"
        elif symb1 == "false":
            result = "true"
        else:
            raise OperandTypeException
        self.data_stack.append(result)

    def INT2CHARS(self):
        try:
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            symb1 = int(symb1)
        except Exception:
            raise StringOperationException
        if symb1 < 0 or symb1 > sys.maxunicode:
            raise StringOperationException
        result = chr(symb1)
        self.data_stack.append(result)

    def STRI2INTS(self):
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        try:
            symb1 = stringConversion(symb1)
            symb2 = int(symb2)
            if symb2 < 0:
                raise StringOperationException
            position = symb1[symb2]
            result = ord(position)
        except Exception:
            raise StringOperationException
        self.data_stack.append(result)

    def JUMPIFEQS(self):
        label_symb = labels()
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if symb1 == "nil" and symb2 == "nil":
            result = True
        elif (symb1 == "nil" and symb2 != "nil") or (symb1 != "nil" and symb2 == "nil"):
            result = False
        else:
            try:
                result = symb1 == symb2
            except Exception:
                raise OperandTypeException

        if result:
            index = jumpToLabel(label_symb)
            return index
        else:
            return i + 1

    def JUMPIFNEQS(self):
        label_symb = labels()
        try:
            symb2 = self.data_stack.pop()
            symb1 = self.data_stack.pop()
        except Exception:
            raise MissingValueException
        if symb1 == "nil" and symb2 == "nil":
            result = False
        elif (symb1 == "nil" and symb2 != "nil") or (symb1 != "nil" and symb2 == "nil"):
            result = True
        else:
            try:
                result = symb1 != symb2
            except Exception:
                raise OperandTypeException

        if result:
            index = jumpToLabel(label_symb)
            return index
        else:
            return i + 1

    def ADD(self):
        """ Sčíta hodnoty rovnakého typu (int/float) a uloží túto hodnotu do premennej
        """
        symb1, symb2, value_type = aritmeticalIntructions(self.global_frame, self.local_frame, self.temporary_frame)
        result = symb1 + symb2
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type)

    def SUB(self):
        """ Odčíta hodnoty rovnakého typu (int/float) a uloží túto hodnotu do premennej
        """
        symb1, symb2, value_type = aritmeticalIntructions(self.global_frame, self.local_frame, self.temporary_frame)
        result = symb1 - symb2
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type)

    def MUL(self):
        """ Vynásobí hodnoty rovnakého typu (int/float) a uloží túto hodnotu do premennej
        """
        symb1, symb2, value_type = aritmeticalIntructions(self.global_frame, self.local_frame, self.temporary_frame)
        result = symb1 * symb2
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type)

    def IDIV(self):
        """ Vydelí hodnoty typu int a uloží túto hodnotu do premennej
        Delenie nulou spôsobí chybu 57
        """
        symb1, symb2, value_type = aritmeticalIntructions(self.global_frame, self.local_frame, self.temporary_frame)
        if value_type == "float":
            raise OperandTypeException
        try:
            result = symb1 // symb2
        except Exception:
            raise ValueOperandException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="int")

    def DIV(self):
        """ Rozšírenie FLOAT
        Vydelí hodnoty typu float a uloží túto hodnotu do premennej
        Delenie nulou spôsobí chybu 57
        """
        symb1, symb2, value_type = aritmeticalIntructions(self.global_frame, self.local_frame, self.temporary_frame)
        if value_type == "int":
            raise OperandTypeException
        try:
            result = symb1 // symb2
        except Exception:
            raise ValueOperandException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="float")

    """ ---------------- Relačné inštrukcie ---------------- """

    def LT(self):
        symb1, symb2, type_symb1, type_symb2 = relationalInstructions(self.global_frame, self.local_frame,
                                                                      self.temporary_frame)
        if symb1 is None or symb2 is None:
            raise OperandTypeException
        result = (str(symb1 < symb2)).lower()
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    def GT(self):
        symb1, symb2, type_symb1, type_symb2 = relationalInstructions(self.global_frame, self.local_frame,
                                                                      self.temporary_frame)
        if symb1 is None or symb2 is None:
            raise OperandTypeException
        result = (str(symb1 > symb2)).lower()
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    def EQ(self):
        symb1, symb2, type_symb1, type_symb2 = relationalInstructions(self.global_frame, self.local_frame,
                                                                      self.temporary_frame)
        if type_symb1 == "nil" and type_symb2 == "nil":
            result = "true"
        elif (type_symb1 == "nil" and type_symb2 != "nil") or (type_symb1 != "nil" and type_symb2 == "nil"):
            result = "false"
        elif symb1 is None or symb2 is None:
            raise OperandTypeException
        else:
            result = (str(symb1 == symb2)).lower()
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    """ ---------------- Booleovské inštrukcie ---------------- """

    def AND(self):
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "bool" and type_symb[2] == "bool":
            text[1] = str(text[1])
            text[2] = str(text[2])
            if text[1] == "true" and text[2] == "true":
                result = "true"
            else:
                result = "false"
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    def OR(self):
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "bool" and type_symb[2] == "bool":
            text[1] = str(text[1])
            text[2] = str(text[2])
            if text[1] == "true" or text[2] == "true":
                result = "true"
            else:
                result = "false"
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    def NOT(self):
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])

        if type_symb[1] == "bool":
            text[1] = str(text[1])
            if text[1] == "true":
                result = "false"
            else:
                result = "true"
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="bool")

    def INT2CHAR(self):
        """ Konvertuje číselnú hodnotu na znak
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])

        if type_symb[1] == "int":
            try:
                tmp = int(text[1])
            except Exception:
                raise StringOperationException
            if tmp < 0 or tmp > sys.maxunicode:
                raise StringOperationException
            result = chr(tmp)
        else:
            raise OperandTypeException

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="string")

    def STRI2INT(self):
        """ Konvertuje znak na ordinálnu hodnotu znaku
        """
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "string":
            try:
                text[1] = stringConversion(text[1])
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException

        if type_symb[2] == "int":
            try:
                text[2] = int(text[2])
                if text[2] < 0:
                    raise StringOperationException
                position = text[1][text[2]]
                result = ord(position)
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="int")

    def INT2FLOAT(self):
        """ Rozšírenie FLOAT
        Konvertuje celé číslo na hexadecimálne číslo
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])
        if type_symb[1] == "int":
            try:
                result = float(text[1])
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="float")

    def FLOAT2INT(self):
        """ Rozšírenie FLOAT
        Konvertuje hexadecimálne číslo na celé číslo
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])
        if type_symb[1] == "float":
            try:
                result = int(float.fromhex(text[1]))
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="int")

    def READ(self):
        """ Načíta jednu hodnotu podľa zadaného typu a uloží túto hodnotu do premennej
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if text[1] == "int":
            try:
                input_var = int(input())
            except:
                text[1] = "nil"
                input_var = "nil"
        elif text[1] == "float":
            try:
                input_var = float.fromhex(input())
            except:
                text[1] = "nil"
                input_var = "nil"
        elif text[1] == "string":
            try:
                input_var = input()
            except:
                text[1] = "nil"
                input_var = "nil"
        elif text[1] == "bool":
            try:
                input_var = input()
                if input_var.lower() == "true":
                    input_var = "true"
                else:
                    input_var = "false"
            except:
                text[1] = "nil"
                input_var = "nil"

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, input_var,
                                                                                 text[1])

    def WRITE(self):
        """ Vypíše hodnotu na štandardný výstup
        """
        type_symb, text = argumentsXML(root, i)
        if type_symb[0] == "var":
            text[0], type_symb[0] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[0])

        if type_symb[0] == "bool":
            if text[0] == "true":
                print("true", end='')
            else:
                print("false", end='')
        elif type_symb[0] == "nil":
            print('', end='')
        elif type_symb[0] == "int":
            print(text[0], end='')
        elif type_symb[0] == "float":
            try:
                print(float.hex(text[0]), end='')
            except:
                print(float.hex(float.fromhex(text[0])), end='')
        else:
            text[0] = stringConversion(text[0])
            print(text[0], end='')

    def CONCAT(self):
        """ Vykoná spojenie dvoch reťazcov do jedného
        """
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "string" and type_symb[2] == "string":
            if text[1] is None:
                text[1] = ""
            if text[2] is None:
                text[2] = ""
            result = text[1] + text[2]
        else:
            raise OperandTypeException

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="string")

    def STRLEN(self):
        """ Zistí počet znakov v reťazci
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])
        if type_symb[1] == "string":
            if text[1] is None:
                text[1] = ""
            result = len(text[1])
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="int")

    def GETCHAR(self):
        """ Do premennej uloží znak na určitej pozícii
        """
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "string" and type_symb[2] == "int":
            try:
                text[2] = int(text[2])
                if text[2] < 0:
                    raise StringOperationException
                result = text[1][text[2]]
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="string")

    def SETCHAR(self):
        """Zmodifikuje znak v reťazci
        """
        type_symb, text = twoOperands(self.global_frame, self.local_frame, self.temporary_frame)
        variable, var_type = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[0])
        if var_type == "string" and type_symb[1] == "int" and type_symb[2] == "string":
            try:
                text[1] = int(text[1])
                text[2] = stringConversion(text[2])
                if text[1] < 0 or text[2] is None:
                    raise StringOperationException
                result = variable[:text[1]] + text[2][0] + variable[text[1] + 1:]
            except Exception:
                raise StringOperationException
        else:
            raise OperandTypeException
        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="string")

    def TYPE(self):
        """ Dynamicky zistí typ symbolu
        """
        type_symb, text = argumentsXML(root, i)
        loadVariable(self.local_frame, self.temporary_frame, text[0])
        if type_symb[1] == "var":
            try:
                text[1], type_symb[1] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[1])
            except:
                value_type = ''
                self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame,
                                                                                         self.local_frame,
                                                                                         self.temporary_frame,
                                                                                         value_type, "string")
                return
        if re.match('^([-+]?\d+)$', str(text[1])):
            result = "int"
        elif re.match('^(true|false)$', str(text[1])):
            result = "bool"
        elif str(text[1]) == "nil":
            result = "nil"
        else:
            result = "string"

        self.global_frame, self.local_frame, self.temporary_frame = saveVariable(self.global_frame, self.local_frame,
                                                                                 self.temporary_frame, result,
                                                                                 value_type="string")

    def LABEL(self):
        pass

    def JUMP(self):
        """ Vykoná nepodmienený skok
        """
        label_symb = labels()
        index = jumpToLabel(label_symb)
        return index

    def JUMPIFEQ(self):
        """ Vykoná podmienený skok
        """
        label_symb = labels()
        symb1, symb2, type_symb1, type_symb2 = relationalInstructions(self.global_frame, self.local_frame,
                                                                      self.temporary_frame)

        if type_symb1 == "nil" and type_symb2 == "nil":
            result = True
        elif (type_symb1 == "nil" and type_symb2 != "nil") or (type_symb1 != "nil" and type_symb2 == "nil"):
            result = False
        elif symb1 is None or symb2 is None:
            raise OperandTypeException
        else:
            result = symb1 == symb2

        if result:
            index = jumpToLabel(label_symb)
            return index
        else:
            return i + 1

    def JUMPIFNEQ(self):
        """ Vykoná podmienený skok
        """
        label_symb = labels()
        symb1, symb2, type_symb1, type_symb2 = relationalInstructions(self.global_frame, self.local_frame,
                                                                      self.temporary_frame)

        if type_symb1 == "nil" and type_symb2 == "nil":
            result = False
        elif (type_symb1 == "nil" and type_symb2 != "nil") or (type_symb1 != "nil" and type_symb2 == "nil"):
            result = True
        elif symb1 is None or symb2 is None:
            raise OperandTypeException
        else:
            result = symb1 != symb2

        if result:
            index = jumpToLabel(label_symb)
            return index
        else:
            return i + 1

    def EXIT(self):
        """ Ukončí vykonávanie programu a ukončí interpret
        """
        type_symb, text = argumentsXML(root, i)
        if type_symb[0] == "var":
            text[0], type_symb[0] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[0])
        if type_symb[0] == "int":
            try:
                text[0] = int(text[0])
                if text[0] < 0 or text[0] > 49:
                    raise ValueOperandException
            except Exception:
                raise ValueOperandException
        else:
            raise OperandTypeException
        exit(text[0])

    def DPRINT(self):
        """ Vypíše zadanú hodnotu na štandardný chybový výstup
        """
        type_symb, text = argumentsXML(root, i)
        if type_symb[0] == "var":
            text[0], type_symb[0] = loadConstant(self.global_frame, self.local_frame, self.temporary_frame, text[0])
        if type_symb[0] == "bool":
            if text[0] == "true":
                print("true", end='', file=sys.stderr)
            else:
                print("false", end='', file=sys.stderr)
        elif type_symb[0] == "nil":
            print('', end='', file=sys.stderr)
        elif type_symb[0] == "int":
            print(text[0], end='', file=sys.stderr)
        elif type_symb[0] == "float":
            try:
                print(float.hex(text[0]), end='', file=sys.stderr)
            except:
                print(float.hex(float.fromhex(text[0])), end='', file=sys.stderr)
        else:
            text[0] = stringConversion(text[0])
            print(text[0], end='', file=sys.stderr)

    def BREAK(self):
        """ Na štandardný chybový výstup vypíše stav interpretu
        """
        print("Pozícia v kóde (order):\t", root[i].get('order'), file=sys.stderr)
        print("Globálny rámec (GF):\t", self.global_frame, file=sys.stderr)
        print("Lokálny rámec  (LF):\t", self.local_frame, file=sys.stderr)
        print("Dočasný rámec  (TF):\t", self.temporary_frame, file=sys.stderr)
        print("Počet vykonaných inštrukcií:", i, file=sys.stderr)


def labels():
    """ Pomocná funkcia pre inštrukcie s návestiami (CALL, JUMP, JUMPIFEQ, JUMPIFNEQ)
    Ak zadané návestie neexistuje, program sa skončí s návratovou hodnotou 52
    """
    type_symb, text = argumentsXML(root, i)
    symb = None
    for j in range(0, len(label_frame)):
        if ''.join(label_frame[j][1]) == text[0]:
            symb = label_frame[j][1]
            break
    if symb is None:
        raise SemanticException
    return symb


def jumpToLabel(label_symb):
    """ Funkcia, ktorá skáče na zadané návestie label_symb
    Vracia hodnotu čísla order
    """
    index = 0
    while True:
        try:
            opcode_tmp = root[index].get('opcode')
            if opcode_tmp == "LABEL" and root[index][0].text == label_symb:
                break
        except:
            break
        index += 1

    return index


def twoOperands(global_frame, local_frame, temporary_frame):
    """ Funkcia, ktorá zistí typ a hodnotu jednej alebo dvoch premenných
    Vracia typ premennej/premenných a hodnotu premennej/premenných
    """
    type_symb, text = argumentsXML(root, i)
    if type_symb[1] == "var" and type_symb[2] == "var":
        text[1], type_symb[1] = loadConstant(global_frame, local_frame, temporary_frame, text[1])
        text[2], type_symb[2] = loadConstant(global_frame, local_frame, temporary_frame, text[2])
    elif type_symb[1] == "var" and type_symb[2] != "var":
        text[1], type_symb[1] = loadConstant(global_frame, local_frame, temporary_frame, text[1])
    elif type_symb[1] != "var" and type_symb[2] == "var":
        text[2], type_symb[2] = loadConstant(global_frame, local_frame, temporary_frame, text[2])

    return type_symb, text


def aritmeticalIntructions(global_frame, local_frame, temporary_frame):
    """ Pomocná funkcia pre aritmetické inštrukcie - int aj float
    """
    type_symb, text = argumentsXML(root, i)
    loadVariable(local_frame, temporary_frame, text[0])

    if type_symb[1] == "var" and type_symb[2] == "var":
        text[1], type_symb[1] = loadConstant(global_frame, local_frame, temporary_frame, text[1])
        text[2], type_symb[2] = loadConstant(global_frame, local_frame, temporary_frame, text[2])
    elif type_symb[1] == "var" and (type_symb[2] == "int" or type_symb[2] == "float"):
        text[1], type_symb[1] = loadConstant(global_frame, local_frame, temporary_frame, text[1])
    elif (type_symb[1] == "int" or type_symb[1] == "float") and type_symb[2] == "var":
        text[2], type_symb[2] = loadConstant(global_frame, local_frame, temporary_frame, text[2])

    if type_symb[1] == "int" and type_symb[2] == "int":
        try:
            symb1 = int(text[1])
            symb2 = int(text[2])
        except Exception:
            raise OperandTypeException
        type_returned = "int"
    elif type_symb[1] == "float" and type_symb[2] == "float":
        try:
            symb1 = float.fromhex(text[1])
            symb2 = float.fromhex(text[2])
        except Exception:
            raise OperandTypeException
        type_returned = "float"
    else:
        raise OperandTypeException

    return symb1, symb2, type_returned


def relationalInstructions(global_frame, local_frame, temporary_frame):
    """ Pomocná funkcia pre relačné inštrukcie
    """
    type_symb, text = twoOperands(global_frame, local_frame, temporary_frame)
    loadVariable(local_frame, temporary_frame, text[0])
    symb1 = symb2 = None

    if type_symb[1] == "int" and type_symb[2] == "int":
        try:
            symb1 = int(text[1])
            symb2 = int(text[2])
        except Exception:
            raise OperandTypeException
    elif type_symb[1] == "bool" and type_symb[2] == "bool":
        if text[1] == "false":
            symb1 = 0
        elif text[1] == "true":
            symb1 = 1
        if text[2] == "false":
            symb2 = 0
        elif text[2] == "true":
            symb2 = 1
    elif type_symb[1] == "string" and type_symb[2] == "string":
        symb1 = stringConversion(text[1])
        symb2 = stringConversion(text[2])

    return symb1, symb2, type_symb[1], type_symb[2]


def loadVariable(local_frame, temporary_frame, text):
    """ Funkcia ktorá zistí, či daný rámec je definovaný
    Ak nie je, program sa ukončí s chybou 55
    """
    frame = ''.join(text)[:2]
    if frame == "GF":
        pass
    elif frame == "LF":
        if local_frame is None:
            raise UndeclaredFrameException
    elif frame == "TF":
        if temporary_frame is None:
            raise UndeclaredFrameException


def loadConstant(global_frame, local_frame, temporary_frame, text):
    """ Funkcia, ktorá zistí typ a hodnotu premennej
    """
    frame = ''.join(text)[:2]
    value = ''.join(text)[3:]
    symb = symb_type = None
    if frame == "GF":
        for j in range(0, len(global_frame)):
            if ''.join(global_frame[j][0]) == value:
                try:
                    symb_type = global_frame[j][1]
                    symb = global_frame[j][2]
                except Exception:
                    raise MissingValueException

        if symb is None:
            raise UndeclaredVariableException

    elif frame == "LF":

        if local_frame is None:
            raise UndeclaredFrameException
        try:
            if local_frame[0][0] != value:
                raise UndeclaredVariableException
        except Exception:
            raise UndeclaredVariableException
        try:
            symb_type = local_frame[0][1]
            symb = local_frame[0][2]
        except Exception:
            raise MissingValueException

    elif frame == "TF":
        if temporary_frame is None:
            raise UndeclaredFrameException
        try:
            temporary_frame.index(value)
        except Exception:
            raise UndeclaredVariableException
        try:
            symb_type = temporary_frame[1]
            symb = temporary_frame[2]
        except Exception:
            raise MissingValueException

    return symb, symb_type


def saveVariable(global_frame, local_frame, temporary_frame, value, value_type):
    """ Uloženie premennej do rámca
    """
    type_symb, text = argumentsXML(root, i)
    frame_var = ''.join(text[0])[:2]
    variable = ''.join(text[0])[3:]
    check = False
    if frame_var == "GF":
        for j in range(0, len(global_frame)):
            if ''.join(global_frame[j][0]) == variable:
                check = True
                break

        if not check:
            raise UndeclaredVariableException
        try:
            global_frame[j].insert(1, value_type)
            global_frame[j].insert(2, value)
        except Exception:
            raise UndeclaredVariableException
        while len(global_frame[j]) > 3:
            global_frame[j].pop()

    elif frame_var == "LF":
        try:
            var_lf = local_frame.pop()
            if ''.join(var_lf[0]) != variable:
                raise UndeclaredVariableException
            local_frame.append(var_lf)
        except Exception:
            raise UndeclaredVariableException

        try:
            local_frame[0][1] = value_type
            local_frame[0][2] = value
        except:
            local_frame[0].append(value_type)
            local_frame[0].append(value)

    elif frame_var == "TF":
        try:
            var_tf = temporary_frame[0]
            if ''.join(var_tf) != variable:
                raise UndeclaredVariableException
        except Exception:
            raise UndeclaredVariableException
        try:
            temporary_frame[1] = value_type
            temporary_frame[2] = value
        except:
            temporary_frame.append(value_type)
            temporary_frame.append(value)

    return global_frame, local_frame, temporary_frame


def stringConversion(text):
    """ Konverzia stringu s escape sekvenciami na string bez escape sekvencií
    """
    symb = text
    if symb is None:
        symb = ''
        return symb
    index_text = 0

    for character in text:
        if character == '\\':
            tmp = text[index_text + 1:index_text + 4]
            try:
                if text[index_text + 1] == '0':
                    tmp = text[index_text + 2:index_text + 4]
                    if text[index_text + 2] == '0':
                        tmp = text[index_text + 3:index_text + 4]
                tmp = chr(int(tmp))
                symb = symb.replace(text[index_text:index_text + 4], tmp)
            except:
                break

        index_text += 1

    return symb


def argumentsXML(root, i):
    """ Pomocná funkcia pre inštrukcie
    Vracia list s typmi operandov a list s hodnotami operandov inštrukcie
    """
    operand = []
    instruction_type = []
    count_args = 1
    for child in list(root[i]):
        operand.append(root[i].find('arg{}'.format(count_args)).text)
        instruction_type.append(child.get('type'))
        count_args += 1

    return instruction_type, operand


def fileExist(file_in):
    """ Nájdenie súbor so vstupmi pre samotnú interpretáciu zadaného zdrojového kódu
    Ak daný súbor neexistuje, program sa ukončí s návratovou hodnotou 11
    """
    try:
        file_out = open(file_in)
    except IOError:
        print("Súbor", file_in, "neexistuje!", file=sys.stderr)
        raise FileInputException
    return file_out


""" ------------------------ LEXIKÁLNA A SYNTAKTICKÁ ANALÝZA ------------------------ """


def countOperands(expected_count, actual_count):
    if expected_count != actual_count:
        raise XMLStructureException


def checkVariable(text, instruction_type):
    if instruction_type != "var" or not re.match('^((GF|LF|TF)@([A-Za-z_\-$&%*!?])([A-Za-z\d_\-$&%*!?]*))$', text):
        raise XMLStructureException


def checkConstant(text, instruction_type):
    if instruction_type != "var" and instruction_type != "nil" and instruction_type != "int" and \
            instruction_type != "float" and instruction_type != "bool" and instruction_type != "string":
        raise XMLStructureException

    if text is None and (instruction_type == "var" or instruction_type == "nil" or instruction_type == "int" or
                         instruction_type == "float" or instruction_type == "bool"):
        raise XMLStructureException

    if (instruction_type == "var" and not re.match('^((GF|LF|TF)@([A-Za-z_\-$&%*!?])([A-Za-z\d_\-$&%*!?]*))$', text)) \
            or \
            (instruction_type == "nil" and text != "nil") or \
            (instruction_type == "int" and not re.match('^([-+]?\d+)$', text)) or \
            (instruction_type == "bool" and not re.match('^(true|false)$', text)):
        raise XMLStructureException
    elif instruction_type == "string":
        if text is None:
            pass
        elif not re.match('^(([^\n\r\\\\\s#]*(\\\\[0-9]{3})?[^\n\r\\\\\s#]*)*)$', text):
            raise XMLStructureException


def checkLabel(text, instruction_type):
    if instruction_type != "label" or not re.match('^([A-Za-z_\-$&%*!?])([A-Za-z\d_\-$&%*!?]*)$', text):
        raise XMLStructureException


def checkType(text, instruction_type):
    if instruction_type != "type" or not re.match('^int|float|string|bool$', text):
        raise XMLStructureException


def checkOpcode(opcode, operand, instruction_type, lst):
    opcode = opcode.lower()

    if opcode == "move" or opcode == "not" or opcode == "int2char" or opcode == "strlen" or opcode == "type" or \
            opcode == "int2float" or opcode == "float2int":
        countOperands(2, len(operand))
        checkVariable(operand[0], instruction_type[0])
        checkConstant(operand[1], instruction_type[1])
    elif opcode == "createframe" or opcode == "pushframe" or opcode == "popframe" or opcode == "return" or \
            opcode == "clears" or opcode == "adds" or opcode == "subs" or opcode == "muls" or opcode == "idivs" or \
            opcode == "lts" or opcode == "gts" or opcode == "eqs" or opcode == "ands" or opcode == "ors" or \
            opcode == "nots" or opcode == "int2chars" or opcode == "stri2ints":
        countOperands(0, len(operand))
    elif opcode == "defvar" or opcode == "pops":
        countOperands(1, len(operand))
        checkVariable(operand[0], instruction_type[0])
    elif opcode == "call" or opcode == "jumpifeqs" or opcode == "jumpifneqs":
        countOperands(1, len(operand))
        checkLabel(operand[0], instruction_type[0])

    elif opcode == "pushs" or opcode == "write":
        countOperands(1, len(operand))
        checkConstant(operand[0], instruction_type[0])

    elif opcode == "add" or opcode == "sub" or opcode == "mul" or opcode == "idiv" or opcode == "div" or \
            opcode == "lt" or opcode == "gt" or opcode == "eq" or \
            opcode == "and" or opcode == "or" or opcode == "stri2int" or \
            opcode == "concat" or opcode == "getchar" or opcode == "setchar":
        countOperands(3, len(operand))
        checkVariable(operand[0], instruction_type[0])
        checkConstant(operand[1], instruction_type[1])
        checkConstant(operand[2], instruction_type[2])

    elif opcode == "read":
        countOperands(2, len(operand))
        checkVariable(operand[0], instruction_type[0])
        checkType(operand[1], instruction_type[1])

    elif opcode == "label":
        countOperands(1, len(operand))
        checkLabel(operand[0], instruction_type[0])
        label_frame.append([])
        for j in range(0, len(label_frame)):
            if not label_frame[j]:
                continue

            elif ''.join(label_frame[j][1]) == operand[0]:
                raise SemanticException
        label_frame[len(label_frame) - 1].append(lst[len(lst) - 1])
        label_frame[len(label_frame) - 1].append(operand[0])

    elif opcode == "jump":
        countOperands(1, len(operand))
        checkLabel(operand[0], instruction_type[0])

    elif opcode == "jumpifeq" or opcode == "jumpifneq":
        countOperands(3, len(operand))
        checkLabel(operand[0], instruction_type[0])
        checkConstant(operand[1], instruction_type[1])
        checkConstant(operand[2], instruction_type[2])
    elif opcode == "exit" or opcode == "dprint":
        countOperands(1, len(operand))
        checkConstant(operand[0], instruction_type[0])

    elif opcode == "break":
        countOperands(0, len(operand))

    else:
        raise XMLStructureException


def sourceXml(source_file):
    """ Funkcia, ktorá slúži na lexikálnu analýzu zadaného súboru s XML
    Funkcia zoradí inštrukcie podľa hodnoty order a taktiež argumenty inštrukcií
    """
    fileExist(source_file)
    try:
        tree = ElementTree.parse(source_file)
        root = tree.getroot()
        x = ElementTree.fromstring(open(source_file).read())
        ElementTree.iterparse(source_file)
        x.find('.')
        x.findall("*")
    except ElementTree.ParseError:
        raise XMLFormatException

    try:
        root[:] = sorted(root, key=lambda child: (child.tag, int(child.get('order'))))
        for child in root:
            child[:] = sorted(child, key=lambda child: (child.tag, child.tag))
    except Exception:
        raise XMLStructureException

    i = 0
    lst = []
    while True:
        try:
            tmp = root[i].attrib['order']
        except:
            break

        if root.tag != "program" or root[i].tag != "instruction":
            raise XMLStructureException
        for name in root.attrib:
            if name != "language" and name != "name" and name != "description":
                raise XMLStructureException

        for name, value in root[i].attrib.items():
            if name != "order" and name != "opcode":
                raise XMLStructureException

        try:
            tmp = int(tmp)
            if tmp <= 0:
                raise ValueError
            lst.append(tmp)
            if lst.count(i) > 1:
                raise ValueError
            if root[i].get('opcode') is None:
                raise XMLStructureException
        except Exception:
            raise XMLStructureException

        count_args = 1
        operand = []
        instruction_type = []
        for child in list(root[i]):
            argument, arg_num = child.tag[:3], child.tag[3:]
            try:
                arg_num = int(arg_num)
                if argument[:3] != "arg" or arg_num <= 0 or arg_num >= 4 or arg_num != count_args:
                    raise ValueError
            except (TypeError, ValueError):
                raise XMLStructureException

            operand.append(root[i].find('arg{}'.format(count_args)).text)
            instruction_type.append(child.get('type'))
            count_args += 1
        checkOpcode(root[i].get('opcode'), operand, instruction_type, lst)
        i += 1

    return root


def show_help():
    """ Funkcia vypíše nápovedu na štandardný výstup
    Vyhodí chybu, ak je parameter --help zadaný s iným parametrom
    """
    if len(sys.argv) != 2:
        raise ParameterException

    print("""Použitie: python3.8 interpret.py [--help] [--source=file] [--input=file]\n
Program načíta XML reprezentáciu programu a tento program s využitím vstupu
podľa parametrov príkazového riadka interpretuje a generuje výstup\n
Parametre príkazového riadka:
  --help\t vypíše túto nápovedu
  --source=file\t vstupný súbor s XML reprezentáciou zdrojového kódu
  --input=file\t súbor so vstupmi pre samotnú interpretáciu zadaného zdrojového kódu\n""")


try:
    """ Hlavná časť programu
    
    Analyzuje parametry s ktorými môže skript pracovať
    """
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise ParameterException

    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        show_help()
        exit(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", nargs='?')
    parser.add_argument("--input", nargs='?')

    try:
        args = parser.parse_args()
    except SystemExit as ex:
        if ex.code == 0:
            exit(0)
        else:
            raise ParameterException()

    input_none = False

    if args.source is None:
        try:
            root = ElementTree.parse(sys.stdin)
            root.getroot()
            root.find('.')
            root.findall("*")
        except ElementTree.ParseError:
            raise XMLFormatException
        exit(0)
    else:
        sourceFile = args.source
        root = sourceXml(sourceFile)

    if args.input is not None:
        my_stdin = sys.stdin
        sys.stdin = open(args.input)

    # Inicializácia triedy Interpretation
    interpretClass = Interpretation(global_frame=[], gf_ind=0, local_frame=None, lf_ind=0,
                                    temporary_frame=None, call_stack=[], data_stack=[])
    i = 0
    while True:
        """ Cyklus postupne spracováva inštrukcie vzostupne podľa poradia order
        
        Hodnota i sa navyšuje každou iteráciou o 1
        Ak je spracovávaná inštrukcia JUMP, JUMPIFEQ, JUMPIFNEQ, CALL, RETURN JUMPIFEQS alebo JUMPIFNEQS,
        hodnota i sa rovná návratovej hodnote z týchto metód triedy Interpretation
        Ak už neexistuje inštrukcia, ktorá by sa mohla spracovať, cyklus sa ukončí
        a program sa ukončí s návratovou hodnotou 0
        """
        try:
            opcode = root[i].attrib['opcode'].upper()
            if opcode == "JUMP" or opcode == "JUMPIFEQ" or \
                    opcode == "JUMPIFNEQ" or opcode == "CALL" or opcode == "RETURN" or \
                    opcode == "JUMPIFEQS" or opcode == "JUMPIFNEQS":
                i = interpretClass.switch(root[i].attrib['opcode'], root, root[i].attrib['order'])
            else:
                interpretClass.switch(root[i].attrib['opcode'], root, root[i].attrib['order'])
                i += 1
        except:
            break
    exit(0)


# ----------------------- Chybové návratové hodnoty -----------------------


except ParameterException:
    print("Zlé parametre!", file=sys.stderr)
    sys.exit(10)
except FileInputException:
    exit(11)
except XMLFormatException:
    print("Chybný XML formát vo vstupnom súbore!", file=sys.stderr)
    exit(31)
except XMLStructureException:
    print("Zlá štruktúra XML!", file=sys.stderr)
    exit(32)

except SemanticException:
    print("Chybná sémantika!", file=sys.stderr)
    exit(52)
except OperandTypeException:
    print("Chybný typ operandu!", file=sys.stderr)
    exit(53)
except UndeclaredVariableException:
    print("Premenná neexistuje!", file=sys.stderr)
    exit(54)
except UndeclaredFrameException:
    print("Rámec neexistuje!", file=sys.stderr)
    exit(55)
except MissingValueException:
    print("Chýbajúca hodnota!", file=sys.stderr)
    exit(56)
except ValueOperandException:
    print("Chybná hodnota operandu!", file=sys.stderr)
    exit(57)
except StringOperationException:
    print("Chybná práca s reťazcom!", file=sys.stderr)
    exit(58)
