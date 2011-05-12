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
        self.stopthread = False
    
    def run(self):
        #print "Start thread"
        while True:
            time.sleep(0.1)
            if self.stopthread:
                print "return cylkus"
                return
            print "cyklus1"
            if self.app != None:
                self.app.progress.pulse()
            p = subprocess.Popen("ls /proc/systemtap/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print "cyklus2"
            if p.stdout:
                print "cyklus3"
                moduleName = p.stdout.read()[0:-1]
                print "cyklus4"
                if moduleName[0:4] == "stap":
                    self.app.moduleName = moduleName
                    #print "konec"
                    break
          #      else:
          #          time.sleep(1)
          #  else:
            print "cyklus5"
            
        print "end cyklus"
        if self.app != None:
            self.app.panely.set_sensitive(True)
            self.app.progress.set_visible(False)
            
    def stop(self):
        self.stopthread = True

        


    
