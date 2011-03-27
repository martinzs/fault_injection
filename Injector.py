#!/usr/bin/env python

import os

class Injector():
    def __init__(self):
        pass
        
    def inject(self, syscalls, command):
        os.system("stap inject.stp \"" + syscalls + "\" -g -c \"" + command + "\"")

def main():
    injector = Injector()
    injector.inject("mkdir a")

if __name__ == "__main__":
    main()
    
