#!/usr/bin/env python
# -*- coding: utf-8 -*-


class GenerateStap():
    def __init__(self):
        pass
    
    def printProbe(self, stap, syscallName, disableSyscalls):
        stap.write("probe syscall." + syscallName +  """
{
    if (pid() == target())
    {""")
        if disableSyscalls == 1:
            stap.write("""
        if (enable_""" + syscallName + """ == 1)
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
        if disableSyscalls == 1:
           stap.write("\n}\n")
        stap.write("""
    }
}

""")
      
    def printProbeReturn(self, stap, args, previousSyscall, disableSyscalls):
        i = 0
        returnCode = ""
        name = ""
        bracketCount = 0
        
        for a in args:
            if i == 0:
                name = a
                if previousSyscall != a:
                    #Druha moznost
                    stap.write("global last_" + a + " = 0\n\n")
                    stap.write("\nprobe syscall." + a + ".return\n{")
                    if disableSyscalls == 1:
                        stap.write("""
    if (enable_""" + a + """ == 1)
    {""")
                    stap.write("""
        if (pid() == target())
        {""")
   
            elif i == 1:
                returnCode = a
            else:
                if a != "''":
                    stap.write("if (syscall_args[" + str(i - 1) + "] == \"" + a + "\")\n{\n")
                    bracketCount += 1
            i += 1
        
        j = 0     
        for c in returnCode:
            stap.write("ecode[" + str(j) + "] = -" + c + "\n")
            j += 1
            
        # Prvni moznost
        #stap.write("$return = ecode[randint(" + str(j) + ")]\n")
        
        #Druha moznost
        stap.write("$return = ecode[last_" + name + "]\n")
        stap.write("last_" + name + "++\n")
        stap.write("if (last_" + name + " == " + str(j) + ")\n")
        stap.write("    last_" + name + " = 0\n")
        
        for j in range(bracketCount):
            stap.write("}\n")
        
    def printProcfs(self, stap, syscallName):
        stap.write("""
global enable_""" + syscallName + """ = 0

probe procfs(\"""" + syscallName + """\").write
{
    if ($value == \"1\\n\")
        enable_""" + syscallName + """ = 1
    else
        enable_""" + syscallName + """ = 0
}
""")
                
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

global ecode

""")

          
    def generate(self, stapFilename, injectedValues, disableSyscalls):
        stap = file(stapFilename, 'w')
        self.printPrologue(stap)
        previousSyscall = ""
        for i in injectedValues:
            if previousSyscall != i[0]:
                if previousSyscall != "":
                    if disableSyscalls == 1:
                        stap.write("}\n}\n}\n\n")
                    else:
                        stap.write("}\n}\n\n")
                if disableSyscalls == 1:
                    self.printProcfs(stap, i[0])
                self.printProbe(stap, i[0], disableSyscalls)  
            self.printProbeReturn(stap, i, previousSyscall, disableSyscalls)
            previousSyscall = i[0]
        if disableSyscalls == 1:
            stap.write("}\n}\n}\n")
        else:
            stap.write("}\n}\n")
        

def main():
    generator = GenerateStap()
    generator.generate()

if __name__ == "__main__":
    main()
    
