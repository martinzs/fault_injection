#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: Injector.py
# Popis:  Spusti vkladani chyb (spousti nastroj Systemtap)
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import os
import sys
import subprocess
import time
import signal
from threading import Thread

import gtk

# Vlakno, ktere spousti Systemtap (vkladani chyb)
class Injector(Thread):

    # command - spousteny program s argumenty
    # stapFilename - jmeno systamtapoveho souboru
    # app - gui aplikace
    def __init__(self, command, stapFilename, app=None):
        Thread.__init__(self)
        self.command = command
        self.stapFilename = stapFilename
        self.app = app
        self.exit = False
        
    
    # beh vlakna
    def run(self):
        self.exit = False
        try:
            self.p = subprocess.Popen("stap " + self.stapFilename + " -g -c \"" + self.command + "\"", shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except OSError:
            if self.app != None:
                gtk.gdk.threads_enter()
                self.app.endTestApp()
                self.app.threadError("Cannot find stap")
                gtk.gdk.threads_leave()

                self.exit = True
            else:
                print "Cannot find stap"
            return
        #os.system("stap " + self.stapFilename + " -g -c \"" + self.command + "\"")
        while self.p.returncode == None:
            if self.exit:
                break        
            output = self.p.stdout.readline()
            if output != None and output != "":
                if output[0:2] == "$$":
                    if self.app != None:
                        gtk.gdk.threads_enter()
                        self.app.addTextToLog(output[2:-1] + "\n")
                        gtk.gdk.threads_leave()
                    else:
                        print output[2:-1]
                elif self.command + ": No such file or directory" in output:
                    gtk.gdk.threads_enter()
                    self.app.endTestApp()
                    self.app.threadError(self.command + ": No such file or directory")
                    gtk.gdk.threads_leave()
                elif "Pass 5: run failed." in output:
                    pass
                elif "WARNING: Number:" in output:
                    pass
                elif "syscall_args[" in output:
                    pass
                elif "Copy failed (" in output:
                    gtk.gdk.threads_enter()
                    self.app.threadError("Permission denied.\nClose application and run as root")
                    gtk.gdk.threads_leave()
                elif "semantic error: no match while resolving probe" in output:
                    pass
                elif "semantic error: probe point mismatch" in output:
                    gtk.gdk.threads_enter()
                    self.app.endTestApp()
                    self.app.threadError("Stap: unknown probe\nDetails are in console")
                    gtk.gdk.threads_leave()
                    print output,
                    return
                else:
                    print output,

            self.p.poll()
        if self.app != None:
            gtk.gdk.threads_enter()
            self.app.endTestApp()
            gtk.gdk.threads_leave()
            self.exit = True
      
    # ukonceni vlakna      
    def terminate(self):
        os.killpg(self.p.pid, signal.SIGINT)
        self.exit = True
       
    # bezi vlakno?
    def isRunning(self):
        return not self.exit
        
