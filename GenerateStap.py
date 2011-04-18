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
        


#global ewouldblock_enable = """ + "1" if enableFault["file"] == "EWOULDBLOCK" else "0" + """
#probe procfs("ewouldblock").write
#{
#    if ($value == "1\n")
#        ewouldblock_enable = 1
#    else
#        ewouldblock_enable = 0
#}

    def generateNormalInjection(self, stapFilename, returnCode, enableFault):
        stap = file(stapFilename, 'w')
        stap.write("""

global eacces_enable = """ + ("1" if enableFault["file"] == "EACCES" else "0") + """
global enoent_enable = """ + ("1" if enableFault["file"] == "ENOENT" else "0") + """
global emfile_enable = """ + ("1" if enableFault["file"] == "EMFILE" else "0") + """
global eexist_enable = """ + ("1" if enableFault["file"] == "EEXIST" else "0") + """

global enetunreach_enable = """ + ("1" if enableFault["net"] == "ENETUNREACH" else "0") + """
global etimedout_enable = """ + ("1" if enableFault["net"] == "ETIMEDOUT" else "0") + """
global econnrefused_enable = """ + ("1" if enableFault["net"] == "ECONNREFUSED" else "0") + """
global econnreset_enable = """ + ("1" if enableFault["net"] == "ECONNRESET" else "0") + """
global emsgsize_enable = """ + ("1" if enableFault["net"] == "EMSGSIZE" else "0") + """
global eisconn_enable = """ + ("1" if enableFault["net"] == "EISCONN" else "0") + """
global enotconn_enable = """ + ("1" if enableFault["net"] == "ENOTCONN" else "0") + """

global eacces_process_enable = """ + ("1" if enableFault["process"] == "EACCES" else "0") + """
global enoent_process_enable = """ + ("1" if enableFault["process"] == "ENOENT" else "0") + """
global enoexec_enable = """ + ("1" if enableFault["process"] == "ENOEXEC" else "0") + """
global enomem_process_enable = """ + ("1" if enableFault["process"] == "ENOMEM" else "0") + """
global elibbad_enable = """ + ("1" if enableFault["process"] == "ELIBBAD" else "0") + """
global etxtbsy_enable = """ + ("1" if enableFault["process"] == "ETXTBSY" else "0") + """


probe procfs("eacces").write
{
    if ($value == "1\\n")
        eacces_enable = 1
    else
        eacces_enable = 0
}

probe procfs("enoent").write
{
    if ($value == "1\\n")
        enoent_enable = 1
    else
        enoent_enable = 0
}

probe procfs("emfile").write
{
    if ($value == "1\\n")
        emfile_enable = 1
    else
        emfile_enable = 0
}



probe procfs("eexist").write
{
    if ($value == "1\\n")
        eexist_enable = 1
    else
        eexist_enable = 0
}

probe procfs("enetunreach").write
{
    if ($value == "1\\n")
        enetunreach_enable = 1
    else
        enetunreach_enable = 0
}

probe procfs("etimedout").write
{
    if ($value == "1\\n")
        etimedout_enable = 1
    else
        etimedout_enable = 0
}

probe procfs("econnrefused").write
{
    if ($value == "1\\n")
        econnrefused_enable = 1
    else
        econnrefused_enable = 0
}

probe procfs("econnreset").write
{
    if ($value == "1\\n")
        econnreset_enable = 1
    else
        econnreset_enable = 0
}

probe procfs("emsgsize").write
{
    if ($value == "1\\n")
        emsgsize_enable = 1
    else
        emsgsize_enable = 0
}

probe procfs("eisconn").write
{
    if ($value == "1\\n")
        eisconn_enable = 1
    else
        eisconn_enable = 0
}

probe procfs("enotconn").write
{
    if ($value == "1\\n")
        enotconn_enable = 1
    else
        enotconn_enable = 0
}


probe procfs("eacces_process").write
{
    if ($value == "1\\n")
        eacces_process_enable = 1
    else
        eacces_process_enable = 0
}

probe procfs("enoent_process").write
{
    if ($value == "1\\n")
        enoent_process_enable = 1
    else
        enoent_process_enable = 0
}

probe procfs("enoexec").write
{
    if ($value == "1\\n")
        enoexec_enable = 1
    else
        enoexec_enable = 0
}

probe procfs("enomem_process").write
{
    if ($value == "1\\n")
        enomem_process_enable = 1
    else
        enomem_process_enable = 0
}

probe procfs("elibbad").write
{
    if ($value == "1\\n")
        elibbad_enable = 1
    else
        elibbad_enable = 0
}

probe procfs("etxtbsy").write
{
    if ($value == "1\\n")
        etxtbsy_enable = 1
    else
        etxtbsy_enable = 0
}


probe syscall.open.return
{
    if (pid() == target())
    {
        if (eacces_enable == 1)
            $return = -""" + returnCode["EACCES"] + """
        else if (enoent_enable == 1)
            $return = -""" + returnCode["ENOENT"] + """
        else if (emfile_enable == 1)
            $return = -""" + returnCode["EMFILE"] + """
        else if (eexist_enable == 1)
            $return =  -""" + returnCode["EEXIST"] + """
    }
}

probe syscall.connect.return
{
    if (pid() == target())
    {
        if (enetunreach_enable == 1)
            $return = -""" + returnCode["ENETUNREACH"] + """
        else if (etimedout_enable == 1)
            $return = -""" + returnCode["ETIMEDOUT"] + """
        else if (econnrefused_enable == 1)
            $return =  -""" + returnCode["ECONNREFUSED"] + """
        else if (eisconn_enable == 1)
            $return = -""" + returnCode["EISCONN"] + """
    }
}

probe syscall.send.return
{
    if (pid() == target())
    {
        if (eisconn_enable == 1)
            $return =  -""" + returnCode["EISCONN"] + """
        else if (enotconn_enable == 1)
            $return =  -""" + returnCode["ENOTCONN"] + """
        else if (econnreset_enable == 1)
            $return =  -""" + returnCode["ECONNRESET"] + """
        else if (emsgsize_enable == 1)
            $return = -""" + returnCode["EMSGSIZE"] + """
    }
}

probe syscall.sendto.return
{
    if (pid() == target())
    {
        if (eisconn_enable == 1)
            $return =  -""" + returnCode["EISCONN"] + """
        else if (enotconn_enable == 1)
            $return =  -""" + returnCode["ENOTCONN"] + """
        else if (econnreset_enable == 1)
            $return =  -""" + returnCode["ECONNRESET"] + """
        else if (emsgsize_enable == 1)
            $return = -""" + returnCode["EMSGSIZE"] + """
    }
}

probe syscall.sendmsg.return
{
    if (pid() == target())
    {
        if (eisconn_enable == 1)
            $return =  -""" + returnCode["EISCONN"] + """
        else if (enotconn_enable == 1)
            $return =  -""" + returnCode["ENOTCONN"] + """
        else if (econnreset_enable == 1)
            $return =  -""" + returnCode["ECONNRESET"] + """
        else if (emsgsize_enable == 1)
            $return = -""" + returnCode["EMSGSIZE"] + """
    }
}

probe syscall.recv.return
{
    if (pid() == target())
    {
        if (econnrefused_enable == 1)
            $return = -""" + returnCode["ECONNREFUSED"] + """
        else if (enotconn_enable == 1)
            $return = -""" + returnCode["ENOTCONN"] + """
    }
}

probe syscall.recvfrom.return
{
    if (pid() == target())
    {
        if (econnrefused_enable == 1)
            $return = -""" + returnCode["ECONNREFUSED"] + """
        else if (enotconn_enable == 1)
            $return = -""" + returnCode["ENOTCONN"] + """
    }
}

probe syscall.recvmsg.return
{
    if (pid() == target())
    {
        if (econnrefused_enable == 1)
            $return = -""" + returnCode["ECONNREFUSED"] + """
        else if (enotconn_enable == 1)
            $return = -""" + returnCode["ENOTCONN"] + """
    }
}
""")
    
