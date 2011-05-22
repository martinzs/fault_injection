#!/usr/bin/env python


import os
import sys
import subprocess
import time
import signal
from threading import Thread

class Injector(Thread):
    def __init__(self, command, stapFilename, app=None):
        Thread.__init__(self)
        self.command = command
        self.stapFilename = stapFilename
        self.app = app
        self.exit = False
    
    def run(self):
        self.exit = False
        self.p = subprocess.Popen("stap " + self.stapFilename + " -g -c \"" + self.command + "\"",  shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE)#, stderr=subprocess.STDOUT)
        #os.system("stap " + self.stapFilename + " -g -c \"" + self.command + "\"")
        while self.p.returncode == None:
            if self.exit:
                break        
            output = self.p.stdout.readline()
            if output != None and output != "":
                if output[0:2] == "$$":
                    if self.app != None:
                        self.app.addTextToLog(output[2:-1] + "\n")
                    else:
                        print output[2:-1]
                else:
                    print output,
                time.sleep(0.1)
            self.p.poll()
        if self.app != None:
            self.app.endTestApp()
            self.exit = True
            
    def terminate(self):
        #self.p.send_signal(signal.SIGINT)
        #try:
        os.killpg(self.p.pid, signal.SIGINT)
        #except KeyboardInterrupt:
        #    pass
        self.exit = True
        
    def isRunning(self):
        return not self.exit
