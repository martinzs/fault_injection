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

from FaultDialog import *

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
        self.builder.connect_signals({ "exitApp" : gtk.main_quit, "browseButtonClicked": self.browseClicked, "nofileRadio" : self.nofileRadioClicked, "eacessRadio" : self.eacessRadioClicked, "enoentRadio" : self.enoentRadioClicked, "emfileRadio" : self.emfileRadioClicked, "ewouldblockRadio" : self.ewouldblockRadioClicked, "eexistRadio" : self.eexistRadioClicked, "nonetRadio" : self.nonetRadioClicked, "enetunreachRadio" : self.enetunreachRadioClicked, "etimedoutRadio" : self.etimedoutRadioClicked, "econnrefusedRadio" : self.econnrefusedRadioClicked, "econnresetRadio" : self.econnresetRadioClicked, "emsgsizeRadio" : self.emsgsizeRadioClicked, "eisconnRadio" : self.eisconnRadioClicked, "enotconnRadio" : self.enotconnRadioClicked, "startButtonClicked" : self.startButtonClicked, "startButtonReleased" : self.startButtonReleased, "termButtonClicked" : self.termButtonClicked, "eaccesProcessRadio" : self.eaccesProcessRadioClicked, "enoentProcessRadio" : self.enoentProcessRadioClicked, "enoexecRadio" : self.enoexecRadioClicked, "enomemProcessRadio" : self.enomemProcessRadioClicked, "elibbadRadio" : self.elibbadRadioClicked, "etxtbsyRadio" : self.etxtbsyRadioClicked, "noprocessRadio" : self.noprocessRadioClicked, "addFaultButton" : self.addFaultButtonClicked})
        button = self.builder.get_object("termButton")
        button.set_sensitive(False)
        self.window = self.builder.get_object("mainWindow")
        self.window.show()
        
        # List of faults
        self.faultView = self.builder.get_object("faultView")
        self.faultList = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.faultView.set_model(self.faultList)
        column = gtk.TreeViewColumn("Syscall", gtk.CellRendererText(), text=0)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("Error", gtk.CellRendererText(), text=1)
        self.faultView.append_column(column)
        cell = gtk.CellRendererToggle()
        cell.set_radio(True)
        #cell.connect("toggled", self.errorToggled, self.faultList)
        column = gtk.TreeViewColumn("Enable", cell, active=2)
        column.set_clickable(True)
        self.faultView.append_column(column)
        
        # extrakce systemovych volani a jejich navratovych hodnot
        extractor = SyscallExtractor()
        self.syscallsAndErrors = extractor.extract("syscalls")
        
        self.enableFault = {}
        self.enableFault["file"] = "NOFAULT"
        self.enableFault["net"] = "NOFAULT"
        self.enableFault["process"] = "NOFAULT"
        
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
        
    def addFaultButtonClicked(self, widget):
        faultDialog = FaultDialog(self.syscallsAndErrors)
        returnValue = faultDialog.run()
        print returnValue
        
        
        
        
    def procfsWriter(self, name, value):
        if self.moduleName != "":
            os.system("echo " + str(value) + " > /proc/systemtap/" + self.moduleName + "/" + name)
       
    def nofileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "NOFILE"
            self.procfsWriter("file", "nofault")

    def eacessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EACCES"
            self.procfsWriter("file", "eacces")

    def enoentRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "ENOENT"
            self.procfsWriter("file", "enoent")
    
    def emfileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EMFILE"
            self.procfsWriter("file", "emfile")
    
    def ewouldblockRadioClicked(self, widget):
        if widget.get_active():
            pass
        else:
            pass
    
    def eexistRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EEXIST"
            self.procfsWriter("file", "eexist")
    
    def nonetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "NOFAULT"
            self.procfsWriter("net", "nofault")

    def enetunreachRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENETUNREACH"
            self.procfsWriter("net", "enetunreach")
    
    def etimedoutRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ETIMEDOUT"
            self.procfsWriter("net", "etimedout")
    
    def econnrefusedRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNREFUSED"
            self.procfsWriter("net", "econnrefused")
    
    def econnresetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNRESET"
            self.procfsWriter("net", "econnreset")
    
    def emsgsizeRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EMSGSIZE"
            self.procfsWriter("net", "emsgsize")
    
    def eisconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EISCONN"
            self.procfsWriter("net", "eisconn")
    
    def enotconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENOTCONN"
            self.procfsWriter("net", "enotconn")

    
    def noprocessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "NOPROCESS"
            self.procfsWriter("process", "nofault")

    def eaccesProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "EACCES"
            self.procfsWriter("process", "eacces_process")

    def enoentProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOENT"
            self.procfsWriter("process", "enoent_process")

    def enoexecRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOEXEC"
            self.procfsWriter("process", "enoexec")

    def enomemProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOMEM"
            self.procfsWriter("process", "enomem_process")

    def elibbadRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ELIBBAD"
            self.procfsWriter("process", "elibbad")

    def etxtbsyRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ETXTBSY"
            self.procfsWriter("process", "etxtbsy")


if __name__ == "__main__":
    sender = SenderStart()
    app = TutorialApp(sender)
    gtk.main()




