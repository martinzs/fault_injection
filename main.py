#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
from SyscallExtractor import *
from InputScanner import *
from Injector import *

def main():
    # kontrola argumentu programu
    inputFilename = ""
    command = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:c:", ["input=", "command="])
    except getopt.GetoptError, e:
        print e
        return
    for o, a in opts:
        if o in ("-i", "--input"):
            inputFilename = a
        elif o in ("-c", "--command"):
            command = a

    if inputFilename == "":
        print "no input file"
        return
    if command == "":
        print "no command"
        return
    
    # otevreni vstupniho souboru
    # a nacteni dat (pravidel pro injection)
    inputData = ""
    try:
        inputFile = file(inputFilename, 'r')
    except IOError:
        print "Soubor neexistuje"
        return
    inputData = inputFile.read()
    inputFile.close()

    # extrakce systemovych volani a jejich navratovych hodnot
    extractor = SyscallExtractor()
    syscallsAndErrors = extractor.extract("syscalls")
        
    # lexikalni analyza vstupniho soboru s pravidly
    scanner = InputScanner(syscallsAndErrors)
    injectValues = scanner.scan(inputData)
    #print injectValues

    # vlozi odpovidajici chyby podle zadaneho vstupu
    injector = Injector()
    injector.inject(injectValues, command)

if __name__ == "__main__":
    main()

