#!/usr/bin/env python

import os
from threading import Thread

class Injector(Thread):
    def __init__(self, syscalls, command):
        Thread.__init__(self)
        self.syscalls = syscalls
        self.command = command
    
    def run(self):
        self.inject()
        
    def inject(self):
        os.system("stap inject3.stp  -g -c \"" + self.command + "\"")
        #os.system("stap ../procfs/procfs.stp")

def main():
    injector = Injector()
    injector.inject("mkdir a")

if __name__ == "__main__":
    main()
    
