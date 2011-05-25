#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: InjectController.py
# Popis:  Sleduje, kdy se prelozi systemtapovy skript
#         a kdy zacne samotne testovani
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import os
import subprocess
import time
from threading import Thread
from threading import Event

import gtk

# Vlakno, ktere rontroluje, kdy se dokonci preklad stap skriptu
# a spusti se samotne testovani
class InjectController(Thread):
    def __init__(self, app=None):
        Thread.__init__(self)
        self.app = app
        self.stopthread = False
    
    # beh vlakna
    def run(self):
        while True:
            time.sleep(0.1)
            if self.stopthread:
                return
            if self.app != None:
                gtk.gdk.threads_enter()
                self.app.progress.pulse()
                gtk.gdk.threads_leave()
            try:
                p = subprocess.Popen("ls /proc/systemtap/", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                if self.app != None:
                    gtk.gdk.threads_enter()
                    self.app.keyboardInterrupt()
                    self.app.threadError("Cannot open external command")
                    gtk.gdk.threads_leave()
                return
            if p.stdout:
                moduleName = p.stdout.read()[0:-1]
                if moduleName[0:4] == "stap":
                    gtk.gdk.threads_enter()
                    self.app.moduleName = moduleName
                    gtk.gdk.threads_leave()
                    break

            
        if self.app != None:
            gtk.gdk.threads_enter()
            self.app.panely.set_sensitive(True)
            self.app.progress.set_visible(False)
            self.app.labelStatus.set_visible(True)
            gtk.gdk.threads_leave()
            
    # ukonceni vlakna   
    def stop(self):
        self.stopthread = True

        


    
