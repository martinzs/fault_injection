#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: SyscallExtractor.py
# Popis:  Extrahuje existujici systemova volani, existujici
#         navratove hodnoty a vzajemne je priradi podle
#         manualovych stranek
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import re
import subprocess
import gzip


# Trida extrahuje existujici systemova volani
# z hlavickovych souboru, dale extrahuje navratove
# hodnoty systemovych volani a priradi tyto hodnoty
# k jednotlivym volanim podle manualovych stranek
class SyscallExtractor():

    def __init__(self):
        self.syscallHeaderFile = "/usr/include/bits/syscall.h"
        self.returnCodeFile1 = "/usr/include/asm-generic/errno.h"
        self.returnCodeFile2 = "/usr/include/asm-generic/errno-base.h"
        
    # Najde systemova volani
    # filename - jmeno hlavickoveho souboru
    # vraci seznam systemovych volani
    def findSyscalls(self, filename):
        f = file(filename, 'r')
        data = f.read()
        f.close()
        r = re.compile("#define[ \t]+SYS_([^ \t]+)")
        syscalls = r.findall(data)
        return syscalls


    # najde navratove hodnoty systemovych volani
    # filename1, filename2 hlavickove soubory
    # vraci asociativni seznam, kde klicem je nazev navratove hodnoty
    def findReturnCode(self, filename1, filename2):
        f = file(filename1, 'r')
        data = f.read()
        f.close()
        f = file(filename2, 'r')
        data += f.read()
        f.close()
#        r = re.compile("#define[ \t]+([A-Z]+)[ \t]+([0-9]+)")
        r = re.compile("#define[ \t]+([A-Z]+)[ \t]+([0-9]+)([ \t]+/\*([^*]+)\*/)?")
        codes = r.findall(data)
        returnCodes = {}
        for code in codes:
            returnCodes[code[0]] = (code[1], code[3])
        return returnCodes


    # najde soubor s manualovou strankou k zadanemu systemovemu volani
    # syscall - systemove volani
    # vraci jmeno souboru, pri chybe None
    def findManPageFile(self, syscall):
        p = subprocess.Popen("man -w 2 " + syscall, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.stdout:
            manPageFile = p.stdout.read()[0:-1]
            return manPageFile
        else:
            return None


    # najde v manualove strance systemoveho volani jeho chyby
    # syscall - systemove volani
    # vraci seznam chyb (textovych retezcu)
    def findErrors(self, syscall):
        manPageFile = self.findManPageFile(syscall)
        if manPageFile:
            data = ""
            if manPageFile.endswith(".gz"):
                f = gzip.open(manPageFile, 'rb')
                data = f.read()
                f.close()
            else:
                f = file(manPageFile, 'r')
                data = f.read()
                f.close()
            
            errors_section = ""
            err_search = re.search("\.SH[ \t]+\"?ERRORS\"?([\w\W]*?)\.SH", data)
            if err_search != None:
                errors_section = err_search.group(1)
            r = re.compile("(\.B[ \t]+|-)(E[A-Z]+)")
            errors = r.findall(errors_section)
            if errors == []:
                return_section = ""
                ret_search = re.search("\.SH[ \t]+\"?RETURN VALUE\"?([\w\W]*?)\.SH", data)
                if ret_search != None:
                    return_section = ret_search.group(1)
                r = re.compile("(\.BR[ \t]+|-)(E[A-Z]+)")
                errors = r.findall(return_section)
            err = []
            for e in errors:
                err.append(e[1])
            return err
        else:
            return []

    # samotne extrahovani
    # postupne vola predchozi metody
    def extract(self, filename):
        syscallsAndErrors = {}
        returnCode = {}
        message = {}
        returnCodeAndMsg = {}
        try:
            syscallFile = file(filename, 'r')
        except IOError:
            syscallFile = file(filename, 'w')
            syscalls = self.findSyscalls(self.syscallHeaderFile)
            syscalls.sort()
            returnCodeAndMsg = self.findReturnCode(self.returnCodeFile1 , self.returnCodeFile2)
            for k in returnCodeAndMsg.keys():
                returnCode[k] = returnCodeAndMsg[k][0]
                message[k] = returnCodeAndMsg[k][1]
            for s in syscalls:
                syscallFile.write(s + ": \n")
                err = self.findErrors(s) 
                errors = {}
                for e in err:
                    try:
                        code = returnCodeAndMsg[e]
                        if e not in errors.keys():
                            errors[e] = code[0]
                            syscallFile.write("\t" + e + "\t" + code[0] + ":\t" + code[1] + "\n")
                    except:
                        pass
                syscall = s.rstrip("at2") 
                if syscall in syscalls and syscall != s:
                    for k in syscallsAndErrors[syscall].keys():
                        code = syscallsAndErrors[syscall][k]
                        if k not in errors.keys():
                            errors[e] = k
                            syscallFile.write("\t" + k + "\t" + code + ":\t" + message[k] + "\n")
                syscallsAndErrors[s] = errors
                syscallFile.write(";\n")
        else:
            data = syscallFile.read()
            rSyscalls = re.compile("(\w+):\s((\s|\S)*?);")
            rErrors = re.compile("\s*(\w+)\t(\d+):\t(.*)\n")
            foundSyscalls = rSyscalls.findall(data)
            for s in foundSyscalls:
                foundErrors = rErrors.findall(s[1])
                errors = {}
                for e in foundErrors:
                    errors[e[0]] = e[1]
                    returnCode[e[0]] = e[1]
                    message[e[0]] = e[2]
                syscallsAndErrors[s[0]] = errors
        return (syscallsAndErrors, returnCode, message)
                
            

def main():
    extractor = SyscallExtractor()
    syscalls = extractor.extract("syscalls")
    #print syscalls

        

if __name__ == "__main__":
    main()

