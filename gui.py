#!/usr/bin/env python


import pygtk
pygtk.require("2.0")
import gtk
import gobject

import os
import subprocess
import time
import signal


from SyscallExtractor import *
#from InputScanner import *
from Injector import *
from InjectController import *
from GenerateStap import *

gtk.gdk.threads_init()

class SenderStart(gobject.GObject):
    def __init__(self):
        self.__gobject_init__()
    
gobject.type_register(SenderStart)
gobject.signal_new("start_signal", SenderStart, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())


class TutorialApp(object):       
    def __init__(self, sender):
        self.sender = sender
        
        self.sender.connect("start_signal", self.startApp)

    
        self.builder = gtk.Builder()
        self.builder.add_from_file("fault_injection.glade")
        self.builder.connect_signals({ "exitApp" : gtk.main_quit, "browseButtonClicked": self.browseClicked, "nofileRadio" : self.nofileRadioClicked, "eacessRadio" : self.eacessRadioClicked, "enoentRadio" : self.enoentRadioClicked, "emfileRadio" : self.emfileRadioClicked, "ewouldblockRadio" : self.ewouldblockRadioClicked, "eexistRadio" : self.eexistRadioClicked, "nonetRadio" : self.nonetRadioClicked, "enetunreachRadio" : self.enetunreachRadioClicked, "etimedoutRadio" : self.etimedoutRadioClicked, "econnrefusedRadio" : self.econnrefusedRadioClicked, "econnresetRadio" : self.econnresetRadioClicked, "emsgsizeRadio" : self.emsgsizeRadioClicked, "eisconnRadio" : self.eisconnRadioClicked, "enotconnRadio" : self.enotconnRadioClicked, "startButtonClicked" : self.startButtonClicked, "startButtonReleased" : self.startButtonReleased, "termButtonClicked" : self.termButtonClicked})
        button = self.builder.get_object("termButton")
        button.set_sensitive(False)
        self.window = self.builder.get_object("mainWindow")
        self.window.show()
        
        # extrakce systemovych volani a jejich navratovych hodnot
        extractor = SyscallExtractor()
        self.syscallsAndErrors = extractor.extract("syscalls")
        
        self.enableFault = {}
        self.enableFault["file"] = "NOFAULT"
        self.enableFault["net"] = "NOFAULT"
        
        self.moduleName = ""
        self.appEntry = self.builder.get_object("appEntry")
        self.paramEntry = self.builder.get_object("paramEntry")
        
        
    
    def browseClicked(self, widget):
        fileDialog = gtk.FileChooserDialog(title=None, action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fileDialog.set_default_response(gtk.RESPONSE_OK)
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            inputApp = self.builder.get_object("appEntry")
            inputApp.set_text(fileDialog.get_filename())
        fileDialog.destroy()
    
    def startButtonReleased(self, widget):
        print "start release"
        time.sleep(3)
        self.panely.set_sensitive(True)
    
    def startApp(self, widget):
        
        
        time.sleep(3)
        print "panely locked"
        # vygeneruje soubor pro systemtap
        #generator = GenerateStap()
        #generator.generateNormalInjection("inject4.stp", self.syscallsAndErrors[1], self.enableFault)
        print "generate finished"
        # vlozi odpovidajici chyby podle zadaneho vstupu
        #injector = Injector(injectValues, command)
        #injector.start()

    
    def startButtonClicked(self, widget):
        widget.set_sensitive(False)
        self.panely = self.builder.get_object("panely")
        self.panely.set_sensitive(False)
        
        termButton = self.builder.get_object("termButton")
        termButton.set_sensitive(True)
        
        # vygeneruje soubor pro systemtap
        generator = GenerateStap()
        generator.generateNormalInjection("inject4.stp", self.syscallsAndErrors[1], self.enableFault)
        
        
        appName = self.appEntry.get_text()  #osetrit prazdne appName
        param = self.paramEntry.get_text()
        self.injector = Injector(appName + " " + param, "inject4.stp", self)
        self.controller = InjectController(self)
        
        self.injector.start()
        self.controller.start()
        
    def endTestApp(self):
        self.moduleName = ""
        self.controller.stop()
        termButton = self.builder.get_object("termButton")
        termButton.set_sensitive(False)
        startButton = self.builder.get_object("startButton")
        startButton.set_sensitive(True)
        self.panely.set_sensitive(True)
        
    def termButtonClicked(self, widget):
        self.endTestApp()
        os.kill(0, signal.SIGINT)
        
        
        
    def procfsWriter(self, name, value):
        if self.moduleName != "":
            os.system("echo " + str(value) + " > /proc/systemtap/" + self.moduleName + "/" + name)
       
    def nofileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "NOFILE"

    def eacessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EACCES"
            self.procfsWriter("eacces", 1)
        else:
            self.procfsWriter("eacces", 0)

    def enoentRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "ENOENT"
            self.procfsWriter("enoent", 1)
        else:
            self.procfsWriter("enoent", 0)
    
    def emfileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EMFILE"
            self.procfsWriter("emfile", 1)
        else:
            self.procfsWriter("emfile", 0)
    
    def ewouldblockRadioClicked(self, widget):
        if widget.get_active():
            pass
        else:
            pass
    
    def eexistRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EEXIST"
            self.procfsWriter("eexist", 1)
        else:
            self.procfsWriter("eexist", 0)
    
    def nonetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "NOFAULT"

    def enetunreachRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENETUNREACH"
            self.procfsWriter("enetunreach", 1)
        else:
            self.procfsWriter("enetunreach", 0)
    
    def etimedoutRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ETIMEDOUT"
            self.procfsWriter("etimedout", 1)
        else:
            self.procfsWriter("etimedout", 0)
    
    def econnrefusedRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNREFUSED"
            self.procfsWriter("econnrefused", 1)
        else:
            self.procfsWriter("econnrefused", 0)
    
    def econnresetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNRESET"
            self.procfsWriter("econnreset", 1)
        else:
            self.procfsWriter("econnreset", 0)
    
    def emsgsizeRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EMSGSIZE"
            self.procfsWriter("emsgsize", 1)
        else:
            self.procfsWriter("emsgsize", 0)
    
    def eisconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EISCONN"
            self.procfsWriter("eisconn", 1)
        else:
            self.procfsWriter("eisconn", 0)
    
    def enotconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENOTCONN"
            self.procfsWriter("enotconn", 1)
        else:
            self.procfsWriter("enotconn", 0)
    
    


if __name__ == "__main__":
    sender = SenderStart()
    app = TutorialApp(sender)
    gtk.main()




