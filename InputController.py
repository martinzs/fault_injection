#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import subprocess
import re
from threading import Thread

class InputController(Thread):
    def __init__(self, injectValues):
        Thread.__init__(self)
        self.syscalls = []
        i = 0
        for value in injectValues:
            if i == 0:
                self.syscalls.append(value[0])
                i += 1
            else:
                if value[0] != self.syscalls[i - 1]:
                    self.syscalls.append(value[0])
                    i += 1
            
    
    def run(self):
        time.sleep(2)
        print "THREAD START"

        while True:
            inputText = raw_input()
            if inputText == "q":
                break
            else:
                module = ""
                p = subprocess.Popen("ls /proc/systemtap/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if p.stdout:
                    module = p.stdout.read()[0:-1]
                else:
                    print "Stap not running, please wait"
                    continue
                command = re.search("e\s+(\w+)\s*", inputText)
                if command != None:
                    if command.group(1) in self.syscalls:
                        os.system("echo 1 > /proc/systemtap/" + module + "/" + command.group(1))
                        #print module
                    else:
                        print "Syscall is not in input rules"
                


