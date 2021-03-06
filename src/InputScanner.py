#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: InputScanner.py
# Popis:  Nacita ulozene chyby (pravidla pro vkladani) ze souboru
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import re

ERROR = -1
START = 0

SYSCALL = 1
L_BRACKET = 2
R_BRACKET = 3
COMMA = 4
MINUS = 5
OR = 6
PARAM = 7
EQUAL = 8
ECODE = 9
ALL = 10
COLON = 11
DIGIT = 12


# Trida pro scanovani vstupniho souboru
# se zadanymi pravidly pro vkladani chyby
class InputScanner():

    # syscallsAndErrors - seznam vsech systemovych volani a
    # jejich navratovych hodnot
    def __init__(self, syscallsAndErrors):
        self.syscallsAndErrors = syscallsAndErrors
        self.syscalls = []
        self.errors = []
        for key in syscallsAndErrors[0]:
            self.syscalls.append(key)
        for key in syscallsAndErrors[1]:
            self.errors.append(key)
        self.scanner = re.Scanner([
            (r"E[A-Z]+", self.ecode),
            (r"ALL", self.all_code),
            (r"\s+", None),
            #(r"\d+", self.digit),
            (r"\w+", self.ident),
            (r"\(", self.l_bracket),
            (r"\)", self.r_bracket),
            (r",", self.comma),
            (r"-", self.minus),
            (r"\|", self.or_op),
            #(r":", self.colon),
            (r"=", self.equal),          
            (r"[^,)(]+", self.param), 
          #  (r"\S+", self.other),
            ])
        
    # identifikator (systemove volani nebo parametr syst. volani)
    # scanner - lexikalni analyzator, viz vyse
    # token - nalezeny retezec (token) podle reg. vyrazu
    def ident(self, scanner, token):
        if token in self.syscalls:
            return (token, SYSCALL)
        else:
            return (token, PARAM)

    # znak leva zavorka
    def l_bracket(self, scanner, token):
        return (token, L_BRACKET)

    #znak prava zavorka
    def r_bracket(self, scanner, token):
        return (token, R_BRACKET)

    #znak carka
    def comma(self, scanner, token):
        return (token, COMMA)
        
    #znak minus (pomlcka)
    def minus(self, scanner, token):
        return (token, MINUS)
        
    #znak | (logicke OR)
    def or_op(self, scanner, token):
        return (token, OR)
        
    def colon(self, scanner, token):
        return (token, COLON)

    #parametr systemoveho volani
    def param(self, scanner, token):
        if token in self.syscalls:
            return (token, SYSCALL)
        else:
            return (token, PARAM)
        
    #znak =
    def equal(self, scanner, token):
        return (token, EQUAL)
        
    #chybovy kod
    def ecode(self, scanner, token):
        if token in self.errors:
            return (token, ECODE)
        else:
            return (token, PARAM)
            
    # ALL u chyboveho kodu
    def all_code(self, scanner, token):
        return (token, ALL)
        
    # cislice
    def digit(self, scanner, token):
        return (token, DIGIT)

    # ostatni
    def other(self, scanner, token):
        return (token, ERROR)

    # syntakticka analyza
    # overi spravnost tokenu
    # tokens - seznam tokenu
    def lex_anal(self, tokens):
        state = START
        for token in tokens[0]:
            if state == START:
                if token[1] == SYSCALL:
                    state = SYSCALL
                else:
                    state = ERROR
                    return 0
                    
            elif state == SYSCALL:    
                if token[1] == L_BRACKET:
                    state = L_BRACKET
                else:
                    state = ERROR
                    return 0
                    
            elif state == L_BRACKET:
                if token[1] == PARAM:
                    state = PARAM
                elif token[1] == MINUS:
                    state = MINUS
                elif token[1] == DIGIT:
                    state = PARAM
                elif token[1] == R_BRACKET:
                    state = R_BRACKET
                else:
                    state = ERROR
                    return 0
                    
            elif state == PARAM:
                if token[1] == COMMA:
                    state = COMMA
                elif token[1] == R_BRACKET:
                    state = R_BRACKET
                else:
                    state = ERROR
                    return 0
                    
            elif state == MINUS:
                if token[1] == COMMA:
                    state = COMMA
                elif token[1] == R_BRACKET:
                    state = R_BRACKET
                else:
                    state = ERROR
                    return 0
                    
            elif state == COMMA:
                if token[1] == PARAM:
                    state = PARAM
                elif token[1] == DIGIT:
                    state = PARAM
                elif token[1] == MINUS:
                    state = MINUS
                else:
                    state = ERROR
                    return 0
                    
            elif state == R_BRACKET:
                if token[1] == EQUAL:
                    state = EQUAL
                else:
                    state = ERROR
                    return 0
                    
            elif state == EQUAL:
                if token[1] == ECODE:
                    state = ECODE
                elif token[1] == ALL:
                    state = ALL
                else:
                    state = ERROR
                    return 0
                    
            elif state == ALL:
                if token[1] == COLON:
                    state = COLON
                elif token[1] == SYSCALL:
                    state = SYSCALL
                else:
                    state = ERROR
                    return 0
                
                    
            elif state == ECODE:
                if token[1] == OR:
                    state = OR
                elif token[1] == SYSCALL:
                    state = SYSCALL
                elif token[1] == COLON:
                    state = COLON
                else:
                    state = ERROR
                    return 0
            
            elif state == OR:
                if token[1] == ECODE:
                    state = ECODE
                else:
                    state = ERROR
                    return 0
                    
            elif state == COLON:
                if token[1] == DIGIT:
                    state = START
                else:
                    state = ERROR
                    return 0
                    
        return 1
        
    # odstrani pocatecni a koncove uvozovky
    def removeQuote(self, param):
        if param[0] == "\"":
            param = param[1:-1]
        elif param[-1] == "\"":
            param = param[0:-2]
        return param
        
    # rozdeli vstupni soubor na tokeny
    # data - obsah vstupniho souboru
    def scan(self, data):
        tokens = self.scanner.scan(data)
        if tokens[0] == []:
            return {}

        if not self.lex_anal(tokens):
            return None
            
        injectValues = {}
        params = []
        paramCount = 0
        notEmptyParam = False
        syscall = ""
        ecode = ""
        for t in tokens[0]:
            if t[1] == SYSCALL:
                if syscall != "":
                    if not notEmptyParam:
                        params = []
                    else:
                        for p in range(paramCount, 6):
                            params.append("")
                    injectValues[syscall].append((ecode, params))
                    params = []
                    ecode = ""
                    notEmptyParam = False
                syscall = t[0]
                if syscall not in injectValues.keys():
                    injectValues[syscall] = []
                
            elif t[1] == PARAM:
                params.append(self.removeQuote(t[0]))
                paramCount += 1
                notEmptyParam = True
            elif t[1] == MINUS:
                params.append("")
                paramCount += 1
            elif t[1] == ECODE:
                ecode = t[0]
        
        if not notEmptyParam:
            params = []
        else:
            for p in range(paramCount, 6):
                params.append("")
        injectValues[syscall].append((ecode, params))
                
        #injectValues.sort()
        return injectValues


def main():
    scanner = InputScanner()
    print scanner.scan("open(-,ahoj ,\"usr/share\") = ENOENT\nmkdirat (-, \"a\", 0777) = ENOTDIR")

if __name__ == "__main__":
    main()
    
