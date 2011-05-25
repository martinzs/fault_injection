#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: GenerateStap.py
# Popis:  Generuje skripty pro Systemtap
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


# Trida, ktera generuje systemtapove skripty
class GenerateStap():

    def __init__(self):
        pass
    
    # vygeneruje probu pro systemove volani
    # stap - otevreny soubor
    # syscallName - jmeno systemoveho volani
    def printProbe(self, stap, syscallName):
        stap.write("probe syscall." + syscallName +  """
{
    if (pid() == target())
    {""")
        stap.write("""
            arguments = argstr
            separatorLength = 0
            i = 1
            token = mytokenize(arguments, ", ")
            while (token != "")
            {        
                if (substr(arguments, 0, 1) == "\\\"")
                    separatorLength = 4
                else
                    separatorLength = 2
                arguments = substr(arguments, strlen(token) + separatorLength, strlen(arguments))
                syscall_args[i] = token
                i++
                token = mytokenize(arguments, ", ")
            }""")
        stap.write("""
    }
}

""")
      
    # vygeneruje return probu pro systemove volani
    # pouziti u aplikace s GUI
    # stap - otevreny soubor
    # syscall - jmeno systemoveho volani
    # errorsAndArgs - pole obsahujici vkladane chyby a argumenty pro porovnani
    # returnCode - asociativni pole obsahujici vsechny dostupne chyby
    def printProbeReturn(self, stap, syscall, errorsAndArgs, returnCode):
        first = True;
        stap.write("""    
probe syscall.""" + syscall + """.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
        
        """)
        for e in errorsAndArgs:
            if first:
                first = False
                try:
                    stap.write("""
        if (""" + syscall + "_" + e[0] + """ == 1)
        {""")
                except KeyError:
                    pass
            else:
                try:
                    stap.write("""
        else if (""" + syscall + "_" + e[0] + """ == 1)
        {""")    
                except KeyError:
                    pass
            i = 0
            bracketCount = 0
            for a in e[1]:
                i += 1
                if a != "":
                    bracketCount += 1
                    stap.write("""
            if (syscall_args[""" + str(i) + "] == \"" + a + """\")
            {""")
            try:
                stap.write("""
            $return = -""" + returnCode[e[0]] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
            """)
            except KeyError:
                pass
            for i in range(bracketCount):
                stap.write("""
            }""")     
            stap.write("""
        }""")   
        stap.write("""
    }
}

""")

    # vygeneruje probu pro systemove volani
    # pouzivano u cmd aplikace - obsahuje mensi rozdily
    # stap - otevreny soubor
    # syscall - jmeno systemoveho volani
    # errorsAndArgs - pole obsahujici vkladane chyby a argumenty pro porovnani
    # returnCode - asociativni pole obsahujici vsechny dostupne chyby
    def printProbeReturnCmdLine(self, stap, syscall, errorsAndArgs, returnCode):
        first = True;
        stap.write("""    
probe syscall.""" + syscall + """.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
        
        """)
        for e in errorsAndArgs:  
            i = 0
            bracketCount = 0
            for a in e[1]:
                i += 1
                if a != "":
                    bracketCount += 1
                    stap.write("""
        if (syscall_args[""" + str(i) + "] == \"" + a + """\")
        {""")
            
            try:
                stap.write("""
        $return = -""" + returnCode[e[0]] + """
        printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        """)
            except KeyError:
                pass
            for i in range(bracketCount):
                stap.write("""
        }""")        
        stap.write("""
    }
}

""")
       

    # vygeneruje procfs.write probu pro systemove volani
    # stap - otevreny soubor
    # syscall - jmeno systemoveho volani
    # errorsAndArgs - pole obsahujici vkladane chyby a argumenty pro porovnani
    # startValue - seznam povolenych volani od zacatku behu aplikace
    def printProcfs(self, stap, syscall, errorsAndArgs, startValue):
        first = True
        for e in errorsAndArgs:
            stap.write("global " + syscall + "_" + e[0] + " = " + ("1" if startValue[syscall] == e[0] else "0") + "\n")
        stap.write("""
probe procfs(\"""" + syscall + """\").write
{
    """)
        for e in errorsAndArgs:
            stap.write(syscall + "_" + e[0] + " = 0\n")

        for e in errorsAndArgs:
            if first:
                first = False
                stap.write("""
    if ($value == \"""" + e[0] + """\\n\")
        """ + syscall + "_" + e[0] + " = 1")
            else:
                stap.write("""
    else if ($value == \"""" + e[0] + """\\n\")
        """ + syscall + "_" + e[0] + " = 1")
        stap.write("""
}

""")
                
    # vypise hlavicku u kazdeho souboru u GUI
    # obshuje funkci na parsovani argumentu syscallu
    def printPrologue(self, stap):    
        stap.write("""global syscall_args
    
function mytokenize:string(input:string, delim:string)
%{ /* unprivileged */
        static char str[MAXSTRINGLEN];
        static char str2[MAXSTRINGLEN];
        static char *str_start;
        static char *str_end;
        char *token = NULL;
        char *token_start = NULL;
        char *token_end = NULL;

        if (THIS->input[0]) {
                strncpy(str, THIS->input, MAXSTRINGLEN);
                strncpy(str2, THIS->input, MAXSTRINGLEN);
                str_start = &str[0];
                str_end = &str[0] + strlen(str);
        }
        if (str[0] == '\\\"')
        {
            token_start = str_start + 1;
            do {
                do {
                        token = strsep(&str_start, "\\\"");
                } while (token && !token[0]);
            } while (token[strlen(token) - 1] == '\\\\');
            str2[(str_start ? str_start : str_end + 1) - token_start] = '\\0';
            token = str2 + 1;
        }
        else
        {
            do {
                    token = strsep(&str_start, THIS->delim);
            } while (token && !token[0]);
            token_start = token;
        }
        if (token) {
                token_end = (str_start ? str_start - 1 : str_end);
                memcpy(THIS->__retvalue, token, token_end - token_start + 1);
        }
%} 

""")

    # generuje systemtapovy soubor pro cmd aplikaci
    # stapFilename - jmeno souboru, do ktereho se bude zapisovat
    # injectedValues - vkladane hodnoty
    # returnCode - asociativni pole vsech navratovych hodnot
    def generateCmdLine(self, stapFilename, injectedValues, returnCode):
        stap = file(stapFilename, 'w')
        self.printPrologue(stap)
        for key in injectedValues.keys():
            self.printProbe(stap, key)
            self.printProbeReturnCmdLine(stap, key, injectedValues[key], returnCode)

    # generuje systemtapovy soubor pro pokrocily mod
    # stapFilename - jmeno souboru, do ktereho se bude zapisovat
    # injectedValues - vkladane hodnoty
    # startValue - seznam povolenych volani od zacatku behu aplikace 
    # returnCode - asociativni pole vsech navratovych hodnot
    def generate(self, stapFilename, injectedValues, startValue, returnCode):
        stap = file(stapFilename, 'w')
        self.printPrologue(stap)
        for key in injectedValues.keys():
            self.printProcfs(stap, key, injectedValues[key], startValue)
            self.printProbe(stap, key)
            self.printProbeReturn(stap, key, injectedValues[key], returnCode)
        

    # generuje systemtapovy soubor pro zakladni mod
    # stapFilename - jmeno souboru, do ktereho se bude zapisovat
    # returnCode - asociativni pole vsech navratovych hodnot
    # enableValue - seznam povolenych volani od zacatku behu aplikace 
    # missingSyscall - systemova volani, ktera nebyla nalezena
    # basicError - obsahuje katerie chyb s volanimi a s vkladanymi chybami
    def generateNormalInjection(self, stapFilename, returnCode, enableFault, missingSyscall, basicError):
        self.basicError = basicError
        stap = file(stapFilename, 'w')
        for key in self.basicError.keys():
            errors = set()
            for s in self.basicError[key].keys():
                for e in self.basicError[key][s]:
                    errors.add(e)
            for e in errors:
                stap.write("global " + e + "_" + key + "_enable = " + ("1" if enableFault[key] == e else "0") + "\n")
        
            stap.write("""
probe procfs(\"""" + key + """\").write
{
                """)
            for e in errors:
                stap.write("""
    """ + e + "_" + key + "_enable = 0""")
            for e in errors:
                stap.write("""
    if ($value == \"""" + e + """\\n\")
        """ + e + "_" + key + """_enable = 1
    else""")
            stap.write("""
    {}
}

""")
        
            for s in self.basicError[key].keys():
                if s not in missingSyscall:
                    stap.write("""
probe syscall.""" + s + """.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)
                    for e in self.basicError[key][s]:
                        try:
                            stap.write("""
        if (""" + e + "_" + key + """_enable == 1)
        {
            $return = -""" + returnCode[e] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
                        except KeyError:
                            pass
            
                    stap.write("""
        {}
    }
}
""")

