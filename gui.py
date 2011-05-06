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
from InputScanner import *

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
        self.builder.connect_signals({ "exitApp" : gtk.main_quit, "browseButtonClicked": self.browseClicked, "nofileRadio" : self.nofileRadioClicked, "eacessRadio" : self.eacessRadioClicked, "enoentRadio" : self.enoentRadioClicked, "emfileRadio" : self.emfileRadioClicked, "ewouldblockRadio" : self.ewouldblockRadioClicked, "eexistRadio" : self.eexistRadioClicked, "nonetRadio" : self.nonetRadioClicked, "enetunreachRadio" : self.enetunreachRadioClicked, "etimedoutRadio" : self.etimedoutRadioClicked, "econnrefusedRadio" : self.econnrefusedRadioClicked, "econnresetRadio" : self.econnresetRadioClicked, "emsgsizeRadio" : self.emsgsizeRadioClicked, "eisconnRadio" : self.eisconnRadioClicked, "enotconnRadio" : self.enotconnRadioClicked, "startButtonClicked" : self.startButtonClicked, "startButtonReleased" : self.startButtonReleased, "termButtonClicked" : self.termButtonClicked, "eaccesProcessRadio" : self.eaccesProcessRadioClicked, "enoentProcessRadio" : self.enoentProcessRadioClicked, "enoexecRadio" : self.enoexecRadioClicked, "enomemProcessRadio" : self.enomemProcessRadioClicked, "elibbadRadio" : self.elibbadRadioClicked, "etxtbsyRadio" : self.etxtbsyRadioClicked, "noprocessRadio" : self.noprocessRadioClicked, "addFaultButton" : self.addFaultButtonClicked, "removeButtonClicked": self.removeButtonClicked, "modeBasicToggled" : self.modeBasicToggled, "modeAdvancedToggled" : self.modeAdvancedToggled, "saveAs" : self.saveAs, "save" : self.save, "open" : self.openFile, "mainDeleteEvent" : self.mainDeleteEvent})
        button = self.builder.get_object("termButton")
        button.set_sensitive(False)
        self.window = self.builder.get_object("mainWindow")
        self.window.show()
        
        # List of faults
        self.faultView = self.builder.get_object("faultView")
        self.faultList = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.faultView.set_model(self.faultList)
        column = gtk.TreeViewColumn("Syscall", gtk.CellRendererText(), text=0)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg1", gtk.CellRendererText(), text=1)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg2", gtk.CellRendererText(), text=2)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg3", gtk.CellRendererText(), text=3)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg4", gtk.CellRendererText(), text=4)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg5", gtk.CellRendererText(), text=5)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("arg6", gtk.CellRendererText(), text=6)
        column.set_resizable(True)
        self.faultView.append_column(column)
        column = gtk.TreeViewColumn("Error", gtk.CellRendererText(), text=7)
        column.set_resizable(True)
        self.faultView.append_column(column)
        cell = gtk.CellRendererToggle()
        cell.set_radio(True)
        cell.connect("toggled", self.faultToggled, self.faultList)
        column = gtk.TreeViewColumn("Enable", cell, active=8)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_alignment(0.5)
        self.faultView.append_column(column)
        
        # extrakce systemovych volani a jejich navratovych hodnot
        extractor = SyscallExtractor()
        self.syscallsAndErrors = extractor.extract("syscalls")
        
        self.enableFault = {}
        self.enableFault["file"] = "NOFAULT"
        self.enableFault["net"] = "NOFAULT"
        self.enableFault["process"] = "NOFAULT"
        
        self.faults = {}
        self.existedFaults = []
        self.faultsStartValue = {}
        self.faultsEdited = False
        self.saveItem = self.builder.get_object("saveItem")
        self.saveAsItem = self.builder.get_object("saveAsItem")
        self.openItem = self.builder.get_object("openItem")
        self.saveItem.set_sensitive(False)
        self.saveAsItem.set_sensitive(False)
        self.openItem.set_sensitive(False)
        self.fileName = None
        
        self.moduleName = ""
        self.appEntry = self.builder.get_object("appEntry")
        self.paramEntry = self.builder.get_object("paramEntry")
        
        # normalni nebo pokracile vkladani
        self.modeBasic = True
        frame = self.builder.get_object("frame2")
        frame.set_visible(False)
        
        
    
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
        self.generateCode()
        
        widget.set_sensitive(False)
        self.panely = self.builder.get_object("panely")
        self.panely.set_sensitive(False)
        
        termButton = self.builder.get_object("termButton")
        termButton.set_sensitive(True)
        
        # vygeneruje soubor pro systemtap
        generator = GenerateStap()
        if self.modeBasic:
            generator.generateNormalInjection("inject4.stp", self.syscallsAndErrors[1], self.enableFault)
        else:
            self.generateCode()
        
        
        appName = self.appEntry.get_text()  #osetrit prazdne appName
        param = self.paramEntry.get_text()
        if self.modeBasic:
            self.injector = Injector(appName + " " + param, "inject4.stp", self)
        else:
            self.injector = Injector(appName + " " + param, "inject5.stp", self)
            
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
        
    def openFile(self, widget):
        fileDialog = gtk.FileChooserDialog(title=None, action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fileDialog.set_default_response(gtk.RESPONSE_OK)
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            filename = fileDialog.get_filename()
            #try:
            inputFile = file(filename, 'r')
            data = inputFile.read()
            scanner = InputScanner(self.syscallsAndErrors)
            self.faults = scanner.scan(data)
            print self.faults
            self.faultList.clear()
            self.existedFaults = []
            self.faultsStartValue = {}
            for key in self.faults.keys():
                self.faultsStartValue[key] = "NOFAULT"
                for f in self.faults[key]:
                    if f[1] == []:
                        self.faultList.append([key, "", "", "", "", "", "", f[0], False])
                    else:
                        self.faultList.append([key, f[1][0], f[1][1], f[1][2], f[1][3], f[1][4], f[1][5], f[0], False])
                    self.existedFaults.append([key, f[0]])
            self.fileName = filename
            self.faultsEdited = False
            self.saveItem.set_sensitive(False)
            #except:
            #    errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format="Cannot open file")
            #    res = errDlg.run()
            #    errDlg.destroy()
        fileDialog.destroy()
    
    def save(self, widget):
        if self.fileName == None:
            self.saveAs(widget)
        else:
            self.saveFaults(self.fileName)
            self.faultsEdited = False
            self.saveItem.set_sensitive(False)
        
    def saveAs(self, widget):
        fileDialog = gtk.FileChooserDialog(title=None, action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        fileDialog.set_default_response(gtk.RESPONSE_OK)
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            filePath = fileDialog.get_filename()
            if os.path.exists(filePath):
                msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="File exists. Do you rewrite this file?")
                res = msgDlg.run()
                msgDlg.destroy()
                if res == gtk.RESPONSE_YES:
                   self.saveFaults(filePath)
                   self.faultsEdited = False
                   self.saveItem.set_sensitive(False)
                else:
                    self.saveAs(widget)
            else:
                self.saveFaults(filePath)
                self.faultsEdited = False
                self.saveItem.set_sensitive(False)
        fileDialog.destroy()
        
    def saveFaults(self, filename):
        print filename
        self.fileName = filename
        outputFile = file(filename, 'w')
        for key in self.faults.keys():
            for f in self.faults[key]:
                argStr = ""
                first = True
                if f[1] != []:
                    for a in f[1]:
                        if first:
                            first = False
                        else:
                            argStr += ", "
                        if a != "":
                            argStr += a
                        else:
                            argStr += "-"
                        
                outputFile.write(key + "(" + argStr + ") = " + f[0] + "\n")
        outputFile.close()
        
    def addFaultButtonClicked(self, widget):
        
        faultDialog = FaultDialog(self.syscallsAndErrors)
        returnValue = faultDialog.run(self.existedFaults)
        print returnValue
        if returnValue[0] == True:
            self.faultsEdited = True
            self.saveItem.set_sensitive(True)
            args = []
            argsEmpty = True
            for a in returnValue[1][2]:
                if a != "":
                    argsEmpty = False
                args.append(a)
            for e in returnValue[1][1]:
                if returnValue[1][0] not in self.faults.keys():
                    self.faults[returnValue[1][0]] = []
                if argsEmpty:
                    self.faults[returnValue[1][0]].append((e, []))
                else:
                    self.faults[returnValue[1][0]].append((e, args))
                self.faultList.append([returnValue[1][0], args[0], args[1], args[2], args[3], args[4], args[5], e, False])
                self.faultsStartValue[returnValue[1][0]] = "NOFAULT"
                self.existedFaults.append([returnValue[1][0], e])
              
                    
            #self.faultList.clear()
            #for f in self.faults:
                
    def generateCode(self):
        print self.faults
        
        #faultsForGen = {}
        #errors = []
        #for f in faults:
        #    if f[0][0] != beforeSyscall:
        #        faultsForGen[f[0][0]] = []
        #        beforeSyscall = f[0][0]
        #    faultsForGen[f[0][0]].append(f[0][1])
        generator = GenerateStap()
        generator.generate("inject5.stp", self.faults, self.faultsStartValue, self.syscallsAndErrors[1])
        
                
    def removeButtonClicked(self, widget):
        path = self.faultView.get_cursor()[0]
        if path != None:
            self.faultsEdited = True
            self.saveItem.set_sensitive(True)
            row = self.faultList.get_iter(path)
            syscall = self.faultList.get_value(row, 0)
            error = self.faultList.get_value(row, 7)
            self.faultList.remove(row)
            del self.existedFaults[int(path[0])]
            try:
                for i in range(len(self.faults[syscall])):
                    if self.faults[syscall][i][0] == error:
                        del self.faults[syscall][i]
                if self.faults[syscall] == []:
                    del self.faults[syscall]
            except KeyError:
                pass
            try:
                if self.faultsStartValue[syscall] == error:
                    self.faultsStartValue[syscall] = "NOFAULT"
            except KeyError:
                pas
            print "ok"
    
    def mainDeleteEvent(self, widget, event):
        if self.faultsEdited:
            msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Faults have been edited. Do you want to save faults?")
            res = msgDlg.run()
            if res == gtk.RESPONSE_YES:
                self.save(widget)
                msgDlg.destroy()
            msgDlg.destroy()
        return False
    
    def faultToggled(self, widget, index, faultList):
        row = faultList.get_iter((int(index),))
        selected = faultList.get_value(row, 8)
        selValue = faultList.get_value(row, 0)

        selected = not selected
        
        r = self.faultList.get_iter_first()
        while r != None:
            value = self.faultList.get_value(r, 0)
            if value == selValue:
                faultList.set(r, 8, False)
            r = self.faultList.iter_next(r)
        
        if selected:
            self.faultsStartValue[selValue] = faultList.get_value(row, 7)
        else:
            self.faultsStartValue[selValue] = "NOFAULT"
        faultList.set(row, 8, selected)
        
    def modeBasicToggled(self, widget):
        if widget.get_active():
            if self.faultsEdited:
                msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Faults have been edited. Do you want to save faults?")
                res = msgDlg.run()
                if res == gtk.RESPONSE_YES:
                    self.save(widget)
                msgDlg.destroy()
            self.modeBasic = True
            frame1 = self.builder.get_object("frame1")
            frame2 = self.builder.get_object("frame2")
            frame1.set_visible(True)
            frame2.set_visible(False)
            self.saveItem.set_sensitive(False)
            self.saveAsItem.set_sensitive(False)
            self.openItem.set_sensitive(False)
            
            self.faults = {}
            self.existedFaults = []
            self.faultsStartValue = {}
            self.faultList.clear()
            

            
    def modeAdvancedToggled(self, widget):
        if widget.get_active():
            self.modeBasic = False
            frame1 = self.builder.get_object("frame1")
            frame2 = self.builder.get_object("frame2")
            frame1.set_visible(False)
            frame2.set_visible(True)
            self.saveItem.set_sensitive(True)
            self.saveAsItem.set_sensitive(True)
            self.openItem.set_sensitive(True)
    
        
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




