#!/usr/bin/env python

import os
import subprocess
import time
from threading import Thread
from threading import Event

class InjectController(Thread):
    def __init__(self, app=None):
        Thread.__init__(self)
        self.app = app
        self.stopthread = Event()
    
    def run(self):
        print "Start thread"
        while True:
            if self.stopthread.isSet():
                return
            print "cyklus"
            p = subprocess.Popen("ls /proc/systemtap/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if p.stdout:
                moduleName = p.stdout.read()[0:-1]
                if moduleName[0:4] == "stap":
                    self.app.moduleName = moduleName
                    print "konec"
                    break
                else:
                    time.sleep(1)
            else:
                time.sleep(1)
        if self.app != None:
            self.app.panely.set_sensitive(True)
            
    def stop(self):
        self.stopthread.set()

        


    
