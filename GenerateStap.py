#!/usr/bin/env python
# -*- coding: utf-8 -*-


class GenerateStap():
    def __init__(self):
        pass
    
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
    def generateCmdLine(self, stapFilename, injectedValues, returnCode):
        stap = file(stapFilename, 'w')
        self.printPrologue(stap)
        for key in injectedValues.keys():
            self.printProbe(stap, key)
            self.printProbeReturnCmdLine(stap, key, injectedValues[key], returnCode)

          
    def generate(self, stapFilename, injectedValues, startValue, returnCode):
        print "generate", injectedValues
        stap = file(stapFilename, 'w')
        self.printPrologue(stap)
        for key in injectedValues.keys():
            self.printProcfs(stap, key, injectedValues[key], startValue)
            self.printProbe(stap, key)
            self.printProbeReturn(stap, key, injectedValues[key], returnCode)
        
        """
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
        """


#global ewouldblock_enable = """ + "1" if enableFault["file"] == "EWOULDBLOCK" else "0" + """
#probe procfs("ewouldblock").write
#{
#    if ($value == "1\n")
#        ewouldblock_enable = 1
#    else
#        ewouldblock_enable = 0
#}

    def generateNormalInjection(self, stapFilename, returnCode, enableFault, missingSyscall):
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

global enomem_memory_enable = """ + ("1" if enableFault["memory"] == "ENOMEM" else "0") + """
global eacces_memory_enable = """ + ("1" if enableFault["memory"] == "EACCES" else "0") + """
global eagain_memory_enable = """ + ("1" if enableFault["memory"] == "EAGAIN" else "0") + """

global ebadf_rw_enable = """ + ("1" if enableFault["rw"] == "EBADF" else "0") + """
global eio_rw_enable = """ + ("1" if enableFault["rw"] == "EIO" else "0") + """
global efbig_rw_enable = """ + ("1" if enableFault["rw"] == "EFBIG" else "0") + """
global enospc_rw_enable = """ + ("1" if enableFault["rw"] == "ENOSPC" else "0") + """


probe procfs("file").write
{
    eacces_enable = 0
    enoent_enable = 0
    emfile_enable = 0
    eexist_enable = 0
    if ($value == "eacces\\n")
        eacces_enable = 1
    else if ($value == "enoent\\n")
        enoent_enable = 1
    else if ($value == "emfile\\n")
        emfile_enable = 1
    else if ($value == "eexist\\n")
        eexist_enable = 1
}


probe procfs("net").write
{
    enetunreach_enable = 0
    etimedout_enable = 0
    econnrefused_enable = 0
    econnreset_enable = 0
    emsgsize_enable = 0
    eisconn_enable = 0
    enotconn_enable = 0

    if ($value == "enetunreach\\n")
        enetunreach_enable = 1
    else if ($value == "etimedout\\n")
        etimedout_enable = 1
    else if ($value == "econnrefused\\n")
        econnrefused_enable = 1
    else if ($value == "econnreset\\n")
        econnreset_enable = 1
    else if ($value == "emsgsize\\n")
        emsgsize_enable = 1
    else if ($value == "eisconn\\n")
        eisconn_enable = 1
    else if ($value == "enotconn\\n")
        enotconn_enable = 1
}


probe procfs("process").write
{
    eacces_process_enable = 0
    enoent_process_enable = 0
    enoexec_enable = 0
    enomem_process_enable = 0
    elibbad_enable = 0
    etxtbsy_enable = 0

    if ($value == "eacces_process\\n")
        eacces_process_enable = 1
    else if ($value == "enoent_process\\n")
        enoent_process_enable = 1
    else if ($value == "enoexec\\n")
        enoexec_enable = 1
    else if ($value == "enomem_process\\n")
        enomem_process_enable = 1
    else if ($value == "elibbad\\n")
        elibbad_enable = 1
    else if ($value == "etxtbsy\\n")
        etxtbsy_enable = 1
}


probe procfs("memory").write
{
    enomem_memory_enable = 0
    eacces_memory_enable = 0
    eagain_memory_enable = 0

    if ($value == "enomem\\n")
        enomem_memory_enable = 1
    else if ($value == "eacces\\n")
        eacces_memory_enable = 1
    else if ($value == "eagain\\n")
        eagain_memory_enable = 1

}

probe procfs("rw").write
{
    ebadf_rw_enable = 0
    eio_rw_enable = 0
    efbig_rw_enable = 0
    enospc_rw_enable = 0

    if ($value == "ebadf\\n")
        ebadf_rw_enable = 1
    else if ($value == "eio\\n")
        eio_rw_enable = 1
    else if ($value == "efbig\\n")
        efbig_rw_enable = 1
    else if ($value == "enospc\\n")
        enospc_rw_enable = 1

}

""")

        if "open" not in missingSyscall:
            stap.write("""
probe syscall.open.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)
            try:
                stap.write("""
        if (eacces_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enoent_enable == 1)
        {
            $return = -""" + returnCode["ENOENT"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (emfile_enable == 1)
        {
            $return = -""" + returnCode["EMFILE"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eexist_enable == 1)
        {
            $return =  -""" + returnCode["EEXIST"] + """
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

        if "connect" not in missingSyscall:
            stap.write("""
probe syscall.connect.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)
            try:
                stap.write("""
        if (enetunreach_enable == 1)
        {
            $return = -""" + returnCode["ENETUNREACH"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (etimedout_enable == 1)
        {
            $return = -""" + returnCode["ETIMEDOUT"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (econnrefused_enable == 1)
        {
            $return =  -""" + returnCode["ECONNREFUSED"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eisconn_enable == 1)
        {
            $return = -""" + returnCode["EISCONN"] + """
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

        if "send" not in missingSyscall:
            stap.write("""
probe syscall.send.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)
        
            try:
                stap.write("""
        if (eisconn_enable == 1)
        {
            $return =  -""" + returnCode["EISCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return =  -""" + returnCode["ENOTCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (econnreset_enable == 1)
        {
            $return =  -""" + returnCode["ECONNRESET"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (emsgsize_enable == 1)
        {
            $return = -""" + returnCode["EMSGSIZE"] + """
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

        if "sendto" not in missingSyscall:
            stap.write("""
probe syscall.sendto.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)

            try:
                stap.write("""
        if (eisconn_enable == 1)
        {
            $return =  -""" + returnCode["EISCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return =  -""" + returnCode["ENOTCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (econnreset_enable == 1)
        {
            $return =  -""" + returnCode["ECONNRESET"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (emsgsize_enable == 1)
        {
            $return = -""" + returnCode["EMSGSIZE"] + """
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

        if "sendmsg" not in missingSyscall:
            stap.write("""
probe syscall.sendmsg.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)

            try:
                stap.write("""
        if (eisconn_enable == 1)
        {
            $return =  -""" + returnCode["EISCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return =  -""" + returnCode["ENOTCONN"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (econnreset_enable == 1)
        {
            $return =  -""" + returnCode["ECONNRESET"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (emsgsize_enable == 1)
        {
            $return = -""" + returnCode["EMSGSIZE"] + """
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

        if "recv" not in missingSyscall:
            stap.write("""
probe syscall.recv.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)

            try:
                stap.write("""
        if (econnrefused_enable == 1)
        {
            $return = -""" + returnCode["ECONNREFUSED"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return = -""" + returnCode["ENOTCONN"] + """
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

        if "recvfrom" not in missingSyscall:
            stap.write("""
probe syscall.recvfrom.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (econnrefused_enable == 1)
        {
            $return = -""" + returnCode["ECONNREFUSED"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return = -""" + returnCode["ENOTCONN"] + """
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


        if "recvmsg" not in missingSyscall:
            stap.write("""
probe syscall.recvmsg.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (econnrefused_enable == 1)
        {
            $return = -""" + returnCode["ECONNREFUSED"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enotconn_enable == 1)
        {
            $return = -""" + returnCode["ENOTCONN"] + """
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
    
        # !!!!!!!!!!! mmap neni v systemtapu
        #if "mmap" not in missingSyscall:
        if False:
            stap.write("""
probe syscall.mmap.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eacces_memory_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eagain_memory_enable == 1)
        {
            $return = -""" + returnCode["EAGAIN"] + """
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

        if "munmap" not in missingSyscall:
            stap.write("""
probe syscall.munmap.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eacces_memory_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eagain_memory_enable == 1)
        {
            $return = -""" + returnCode["EAGAIN"] + """
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

        if "mmap2" not in missingSyscall:
            stap.write("""
probe syscall.mmap2.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eacces_memory_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eagain_memory_enable == 1)
        {
            $return = -""" + returnCode["EAGAIN"] + """
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

        if "mprotect" not in missingSyscall:
            stap.write("""
probe syscall.mprotect.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eacces_memory_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
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

        if "mremap" not in missingSyscall:
            stap.write("""
probe syscall.mremap.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
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

        if "brk" not in missingSyscall:
            stap.write("""
probe syscall.brk.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_memory_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
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


        if "write" not in missingSyscall:
            print "write"
            stap.write("""
probe syscall.write.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)

            try:
                stap.write("""
        if (ebadf_rw_enable == 1)
        {
            $return =  -""" + returnCode["EBADF"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eio_rw_enable == 1)
        {
            $return =  -""" + returnCode["EIO"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (efbig_rw_enable == 1)
        {
            $return =  -""" + returnCode["EFBIG"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enospc_rw_enable == 1)
        {
            $return = -""" + returnCode["ENOSPC"] + """
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

        if "read" not in missingSyscall:
            stap.write("""
probe syscall.read.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return

        """)

            try:
                stap.write("""
        if (ebadf_rw_enable == 1)
        {
            $return =  -""" + returnCode["EBADF"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (eio_rw_enable == 1)
        {
            $return =  -""" + returnCode["EIO"] + """
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

        if "execve" not in missingSyscall:
            stap.write("""
probe syscall.execve.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (eacces_process_enable == 1)
        {
            $return = -""" + returnCode["EACCES"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enoent_process_enable == 1)
        {
            $return = -""" + returnCode["ENOENT"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enoexec_enable == 1)
        {
            $return = -""" + returnCode["ENOEXEC"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (enomem_process_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (elibbad_enable == 1)
        {
            $return = -""" + returnCode["ELIBBAD"] + """
            printf("$$%s () = %d %s -> %d %s\\n", name, returnOld, errno_str(errnoOld), $return, errno_str($return))
        }
        else """)
            except KeyError:
                pass
            try:
                stap.write("""
        if (etxtbsy_enable == 1)
        {
            $return = -""" + returnCode["ETXTBSY"] + """
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

        if "fork" not in missingSyscall:
            stap.write("""
probe syscall.fork.return
{
    if (pid() == target())
    {
        returnOld = $return
        if ($return >= 0)
            errnoOld = 0
        else
            errnoOld = $return
            
        """)
            try:
                stap.write("""
        if (enomem_process_enable == 1)
        {
            $return = -""" + returnCode["ENOMEM"] + """
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


