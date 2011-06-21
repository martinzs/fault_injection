#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: fi-cmd.py
# Popis:  Hlavni funkce konzolove aplikace
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import sys
import getopt
from SyscallExtractor import *
from InputScanner import *
from Injector import *
from GenerateStap import *

# hlavni funkce konzolove aplikace
def main():
    # kontrola argumentu programu
    inputFilename = ""
    command = ""
    injectFile = "inject-cmd.fi"

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
        print "File does not exist."
        return
    inputData = inputFile.read()
    inputFile.close()

    # extrakce systemovych volani a jejich navratovych hodnot
    extractor = SyscallExtractor()
    try:
        syscallsAndErrors = extractor.extract("syscalls")
    except:
        print "Error during syscalls search"
        return
        
    # lexikalni a syntakticka analyza vstupniho soboru s pravidly
    scanner = InputScanner(syscallsAndErrors)
    injectValues = scanner.scan(inputData)
    if injectValues == None:
        print "Bad format of input file"
        return

    # vygeneruje soubor pro systemtap
    generator = GenerateStap()
    generator.generateCmdLine(injectFile, injectValues, syscallsAndErrors[1])

    # vlozi odpovidajici chyby podle zadaneho vstupu
    injector = Injector(command, injectFile)
    try:
        injector.start()
    except:
        print "Error during injection"



    
    
    
    

if __name__ == "__main__":
    main()

