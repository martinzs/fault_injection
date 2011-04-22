#!/usr/bin/env python


import os
import subprocess
import time
from threading import Thread

class Injector(Thread):
    def __init__(self, command, stapFilename, app=None):
        Thread.__init__(self)
        self.command = command
        self.stapFilename = stapFilename
        self.app = app
    
    def run(self):
        os.system("stap " + self.stapFilename + " -g -c \"" + self.command + "\"")
        if self.app != None:
            self.app.endTestApp()
        
