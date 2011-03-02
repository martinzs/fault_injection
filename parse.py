#!/usr/bin/env python

import re
import subprocess
import gzip

# Najde systemova volani
# filename - jmeno hlavickoveho souboru
# vraci seznam systemovych volani
def findSyscalls(filename):
    f = file(filename, 'r')
    data = f.read()
    f.close()
    r = re.compile("#define[ \t]+SYS_([^ \t]+)")
    syscalls = r.findall(data)
    return syscalls


# najde navratove hodnoty systemovych volani
# filename1, filename1 hlavickove soubory
# vraci asociativni seznam, kde klicem je nazev navratove hodnoty
def findReturnCode(filename1, filename2):
    f = file(filename1, 'r')
    data = f.read()
    f.close()
    f = file(filename2, 'r')
    data += f.read()
    f.close()
    r = re.compile("#define[ \t]+([A-Z]+)[ \t]+([0-9]+)")
    codes = r.findall(data)
    returnCodes = {}
    for code in codes:
        returnCodes[code[0]] = code[1]
    return returnCodes


# najde soubor s manualovou strankou k zadanemu systemovemu volani
# syscall - systemove volani
# vraci jmeno souboru, pri chybe None
def findManPageFile(syscall):
    p = subprocess.Popen("man -w 2 " + syscall, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        manPageFile = p.stdout.read()[0:-1]
        return manPageFile
    else:
        return None


# najde v manualove strance systemoveho volani jeho chyby
# syscall - systemove volani
# vraci seznam chyb (textovych retezcu)
def findErrors(syscall):
    manPageFile = findManPageFile(syscall)
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


def main():
    syscalls = findSyscalls("/usr/include/bits/syscall.h")
    returnCode = findReturnCode("/usr/include/asm-generic/errno.h", "/usr/include/asm-generic/errno-base.h")
    for s in syscalls:
        print s
        err = findErrors(s) 
        for e in err:
            try:
                print "\t", e, returnCode[e]
            except:
                pass
        

if __name__ == "__main__":
    main()

