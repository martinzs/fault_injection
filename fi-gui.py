#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: fi-gui.py
# Popis:  Graficke uzivatelske rozhrani - hlavni okno
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz


import pygtk
pygtk.require("2.0")
import gtk
import gobject

import os
import subprocess
import time
import signal


from SyscallExtractor import *
from Injector import *
from InjectController import *
from GenerateStap import *
from InputScanner import *

from FaultDialog import *

gtk.gdk.threads_init()


class TutorialApp(object):       
    def __init__(self):
        
        self.injectBasicFilename = "injectBasic.stp"
        self.injectAdvancedFilename = "injectAdvanced.stp"
        
        self.injector = None
        self.controller = None
    
        self.builder = gtk.Builder()
        self.builder.add_from_file("fault_injection.glade")
        # signaly z glade souboru
        self.builder.connect_signals({ "exitApp" : gtk.main_quit, "browseButtonClicked": self.browseClicked,
                                    "nofileRadio" : self.nofileRadioClicked, "eacessRadio" : self.eacessRadioClicked,
                                    "enoentRadio" : self.enoentRadioClicked, "emfileRadio" : self.emfileRadioClicked,
                                    "ewouldblockRadio" : self.ewouldblockRadioClicked, "eexistRadio" : self.eexistRadioClicked,
                                    "nonetRadio" : self.nonetRadioClicked, "enetunreachRadio" : self.enetunreachRadioClicked,
                                    "etimedoutRadio" : self.etimedoutRadioClicked, "econnrefusedRadio" : self.econnrefusedRadioClicked,
                                    "econnresetRadio" : self.econnresetRadioClicked, "emsgsizeRadio" : self.emsgsizeRadioClicked,
                                    "eisconnRadio" : self.eisconnRadioClicked, "enotconnRadio" : self.enotconnRadioClicked,
                                    "startButtonClicked" : self.startButtonClicked, "termButtonClicked" : self.termButtonClicked,
                                    "eaccesProcessRadio" : self.eaccesProcessRadioClicked, "enoentProcessRadio" : self.enoentProcessRadioClicked,
                                    "enoexecRadio" : self.enoexecRadioClicked, "enomemProcessRadio" : self.enomemProcessRadioClicked,
                                    "elibbadRadio" : self.elibbadRadioClicked, "etxtbsyRadio" : self.etxtbsyRadioClicked,
                                    "noprocessRadio" : self.noprocessRadioClicked, "addFaultButton" : self.addFaultButtonClicked,
                                    "removeButtonClicked": self.removeButtonClicked, "modeBasicToggled" : self.modeBasicToggled,
                                    "modeAdvancedToggled" : self.modeAdvancedToggled, "saveAs" : self.saveAs, "save" : self.save,
                                    "open" : self.openFile, "mainDeleteEvent" : self.mainDeleteEvent, "noMemoryRadio" : self.noMemoryRadioClicked,
                                    "memoryEnomemRadio" : self.memoryEnomemRadioClicked, "memoryEaccesRadio" : self.memoryEaccesRadioClicked,
                                    "memoryEagainRadio" : self.memoryEagainRadioClicked, "noRwRadio" : self.noRwRadioClicked,
                                    "rwEbadfRadio" : self.rwEbadfRadioClicked, "rwEioRadio" : self.rwEioRadioClicked,
                                    "rwEfbigRadio" : self.rwEfbigRadioClicked, "rwEnospcRadio" : self.rwEnospcRadioClicked,
                                    "fileENOTDIRRadio" : self.fileENOTDIRRadioClicked, "fileEBUSYRadio" : self.fileEBUSYRadioClicked,
                                    "fileENOTEMPTYRadio" : self.fileENOTEMPTYRadioClicked, "fileEMLINKRadio" : self.fileEMLINKRadioClicked,
                                    "runAbout" : self.runAbout, "textViewAllocate" : self.scrollDown})
                                    
        button = self.builder.get_object("termButton")
        button.set_sensitive(False)
        self.window = self.builder.get_object("mainWindow")
        self.window.show()
        
        
        # Tabulka pro chyby v pokrocilem rezimu
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
        
        # asociativni pole pro povolene chyby od zacatku testovani
        # v zakladnim rezimu
        self.enableFault = {}
        self.enableFault["file"] = "NOFAULT"
        self.enableFault["net"] = "NOFAULT"
        self.enableFault["process"] = "NOFAULT"
        self.enableFault["memory"] = "NOFAULT"
        self.enableFault["rw"] = "NOFAULT"
        
        # datove typy pro chyby v pokrocilem rezimu
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
        
        # log pro aktualni chyby
        self.logText = ""
        self.textBuffer = self.builder.get_object("textBuffer")
        self.logView = self.builder.get_object("textViewLog")
        
        # jmeno systemtapoveho modulu v procfs
        self.moduleName = ""
        
        # jmeno aplikace a jeji argumenty
        self.appEntry = self.builder.get_object("appEntry")
        self.paramEntry = self.builder.get_object("paramEntry")
        
        # normalni nebo pokracile vkladani
        self.modeBasic = True
        frame = self.builder.get_object("frame2")
        frame.set_visible(False)
        
        
        # vkladane chyby do zakladniho modu
        self.basicError = {}
        self.basicError["file"] = { "open" : ["EACCES", "ENOENT", "EMFILE", "EEXIST"],
                                    "creat" : ["EACCES", "ENOENT", "EMFILE", "EEXIST"],
                                    "mkdir" : ["EACCES", "ENOENT", "ENOTDIR", "EEXIST"],
                                    "mkdirat" : ["EACCES", "ENOENT", "ENOTDIR", "EEXIST"],
                                    "chmod" : ["EACCES", "ENOENT", "ENOTDIR"],
                                    "chmodat" : ["EACCES", "ENOENT", "ENOTDIR"],
                                    "chown" : ["EACCES", "ENOENT", "ENOTDIR"],
                                    "fchown" : ["EACCES", "ENOENT", "ENOTDIR"],
                                    "lchown" : ["EACCES", "ENOENT", "ENOTDIR"],
                                    "rmdir" : ["EACCES", "ENOENT", "ENOTDIR", "EBUSY", "ENOTEMPTY"],
                                    "link" : ["EACCES", "ENOENT", "ENOTDIR", "EEXIST", "EMLINK"],
                                    "linkat" : ["EACCES", "ENOENT", "ENOTDIR", "EEXIST", "EMLINK"]}
        self.basicError["net"] = {  "connect" : ["ENETUNREACH", "ETIMEDOUT", "ECONNREFUSED", "EISCONN"],
                                    "send" : ["ECONNRESET", "EMSGSIZE", "EISCONN", "ENOTCONN"],
                                    "sendto" : ["ECONNRESET", "EMSGSIZE", "EISCONN", "ENOTCONN"],
                                    "sendmsg" : ["ECONNRESET", "EMSGSIZE", "EISCONN", "ENOTCONN"],
                                    "recv" : ["ECONNREFUSED", "ENOTCONN"],
                                    "recvfrom" : ["ECONNREFUSED", "ENOTCONN"],
                                    "recvmsg" : ["ECONNREFUSED", "ENOTCONN"]}
        self.basicError["process"] = {"execve" : ["EACCES", "ENOENT", "ENOEXEC", "ENOMEM", "ELIBBAD", "ETXTBSY"],
                                      "fork" : ["ENOMEM"]}
        self.basicError["memory"] = {"mmap2" : ["ENOMEM", "EACCES", "EAGAIN"],
                                     "munmap" : ["ENOMEM", "EACCES", "EAGAIN"],
                                     "mremap" : ["EAGAIN"],
                                     "mprotect" : ["EACCES", "EAGAIN"],
                                     "brk" : ["EAGAIN"]}
        self.basicError["rw"] = {"write" : ["EBADF", "EIO", "EFBIG", "ENOSPC"],
                                 "read" : ["EBADF", "EIO"]}
        
        # chybejici volani v zakladnim rezim
        self.missingSyscall = []
        
        # zkontroluje, ktere volani v zakldnim rezimu nelze pouzit
        self.checkError()
        
        # stav aplikace
        self.progress = self.builder.get_object("progressbar")
        self.imageYes =self.builder.get_object("imageYes")
        self.imageYes.set_visible(False)
        self.imageNo =self.builder.get_object("imageNo")
        self.labelStatus = self.builder.get_object("labelStatus")
        
        
        
    # zkontroluje, ktera volani a ktere chyby nejsou dostupne
    # v zakladnim rezimu
    # ty, ktere chybi nelze vybrat
    def checkError(self):
        syscalls = self.syscallsAndErrors[0].keys()
        
        for key in self.basicError.keys():
            checkSyscalls = []
            existSyscalls = {}
            errors = set()
            for s in self.basicError[key].keys():
                checkSyscalls.append(s)
                for e in self.basicError[key][s]:
                    errors.add(e)
        
            exists = False
            for s in checkSyscalls:
                if s in syscalls:
                    exists = True
                    existSyscalls[s] = self.syscallsAndErrors[0][s]
                else:
                    self.missingSyscall.append(s)
            if not exists:
                try:
                    vbox = self.builder.get_object("vbox" + key)
                    vbox.set_sensitive(False)
                    continue
                except:
                    pass
                
            
            for e in errors:
                exists = False
                for s in existSyscalls.keys():
                    if e in existSyscalls[s]:
                        exists = True    
                        break
                        
                if not exists:
                    try:
                        errorRadio = self.builder.get_object(key + e + "Radio")
                        errorRadio.set_sensitive(False)
                    except:
                        pass
                
    
    # zobrazi about dialog
    def runAbout(self, widget):
        about = gtk.AboutDialog()
        about.set_program_name("Fault injection tool")
        about.set_copyright("(c) Martin Zelinka")
        about.set_comments("A Fault Injection Bug Hunting Tool Based on Systemtap")
        about.run()
        about.destroy()

    # tlacitko Browse pro vybrani testovaneho programu
    def browseClicked(self, widget):
        fileDialog = gtk.FileChooserDialog(title=None, action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fileDialog.set_default_response(gtk.RESPONSE_OK)
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            inputApp = self.builder.get_object("appEntry")
            inputApp.set_text(fileDialog.get_filename())
        fileDialog.destroy()


    # tlacitko Run, spusti testovani
    def startButtonClicked(self, widget):
        appName = self.appEntry.get_text()
        param = self.paramEntry.get_text()
        
        if appName == "":
            messDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format="Path to aplication is empty")
            messDlg.run()
            messDlg.destroy()
            return
            
        if not self.modeBasic:
            if self.faults == {}:
                messDlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_CLOSE, message_format="No fault is added")
                messDlg.run()
                messDlg.destroy()
                return
            
        # nastavi se zobrazovany stav
        self.progress.set_fraction(0.0)
        self.progress.set_visible(True)
        self.labelStatus.set_label("Running")
        self.imageYes.set_visible(True)
        self.imageNo.set_visible(False)
        
        # vyprazdni se Log
        self.logText = ""
        self.textBuffer.set_text(self.logText)
        
        # zneplatni se tlacitka a vkladane chyby
        widget.set_sensitive(False)
        self.addButton = self.builder.get_object("addButton")
        self.addButton.set_sensitive(False)
        self.removeButton = self.builder.get_object("removeButton")
        self.removeButton.set_sensitive(False)
        self.browseButton = self.builder.get_object("browseButton")
        self.browseButton.set_sensitive(False)
        self.panely = self.builder.get_object("panely")
        self.panely.set_sensitive(False)
        self.menu = self.builder.get_object("menubar1")
        self.menu.set_sensitive(False)
        
        termButton = self.builder.get_object("termButton")
        termButton.set_sensitive(True)
        
        # vygeneruje soubor pro systemtap
        generator = GenerateStap()
        try:
            if self.modeBasic:
                generator.generateNormalInjection(self.injectBasicFilename, self.syscallsAndErrors[1], self.enableFault, self.missingSyscall, self.basicError)
            else:
                generator.generate(self.injectAdvancedFilename, self.faults, self.faultsStartValue, self.syscallsAndErrors[1])
        except IOError:
            self.endTestApp()
            self.threadError("Permission denied.\nClose application and run as root")
            return
                
        # vytvoreni injectoru, ktery spousti testovani (Systemtap)
        if self.modeBasic:
            self.injector = Injector(appName + " " + param, self.injectBasicFilename, self)
        else:
            self.injector = Injector(appName + " " + param, self.injectAdvancedFilename, self)
            
        # vytvoreni kontroleru, zjisti, kdy skonci predklad skriptu
        # pro Systemtap
        self.controller = InjectController(self)
        
        # spusti se testovani
        self.injector.start()
        self.controller.start()
        
        
    # vola se na konci testovani, nastavi stav aplikace apod   
    def endTestApp(self):
        self.moduleName = ""
        if self.controller != None:
            self.controller.stop()
        termButton = self.builder.get_object("termButton")
        termButton.set_sensitive(False)
        startButton = self.builder.get_object("startButton")
        startButton.set_sensitive(True)
        self.panely.set_sensitive(True)
        self.progress.set_visible(False)
        
        self.labelStatus.set_label("Stopped")
        self.labelStatus.set_visible(True)
        self.imageYes.set_visible(False)
        self.imageNo.set_visible(True)
        
        self.addButton = self.builder.get_object("addButton")
        self.addButton.set_sensitive(True)
        self.removeButton = self.builder.get_object("removeButton")
        self.removeButton.set_sensitive(True)
        self.browseButton = self.builder.get_object("browseButton")
        self.browseButton.set_sensitive(True)
        self.menu = self.builder.get_object("menubar1")
        self.menu.set_sensitive(True)
        
    # tlacitko Terminate pro ukonceni testovani
    def termButtonClicked(self, widget):
        if self.injector != None:
            self.injector.terminate()
        
    # vola se pri Ctrl + C
    def keyboardInterrupt(self):
        if self.injector != None:
            self.injector.terminate()
          
    # vola se z ostatnich vlaken
    # pokud nastane chyba
    # msg - chybove hlaseni
    def threadError(self, msg):
        errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE, message_format=msg)
        errDlg.run()
        errDlg.destroy()
        
    # otevre soubor s preddefinovanymi chybami
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
            if self.faults == None:
                fileDialog.destroy()
                self.threadError("Bad file format")
                return
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
        fileDialog.destroy()
    
    # ulozi soubor s preddefinovanymi chybami
    def save(self, widget):
        if self.fileName == None:
            self.saveAs(widget)
        else:
            self.saveFaults(self.fileName)
            self.faultsEdited = False
            self.saveItem.set_sensitive(False)
        
    # ulozi chyby do soubru
    def saveAs(self, widget):
        fileDialog = gtk.FileChooserDialog(title=None, action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        fileDialog.set_default_response(gtk.RESPONSE_OK)
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            filePath = fileDialog.get_filename()
            if os.path.exists(filePath):
                msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="File exists. Do you want to overwrite this file?")
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
        
    # zapise chyby do souboru
    def saveFaults(self, filename):
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
        
    # prida chybu v pokrocilem rezimu
    # vytvori se dialog Add fault
    def addFaultButtonClicked(self, widget):
        
        faultDialog = FaultDialog(self.syscallsAndErrors)
        returnValue = faultDialog.run(self.existedFaults)
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
              
        
    # odstani chybu z tabulky v pokrocilem rezimu  
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
                        break
                if self.faults[syscall] == []:
                    del self.faults[syscall]
            except KeyError:
                pass
            try:
                if self.faultsStartValue[syscall] == error:
                    self.faultsStartValue[syscall] = "NOFAULT"
            except KeyError:
                pass
    
    # vola se pred ukoncenim aplikace
    # kontrola jestli jsou ulozeny chyby
    def mainDeleteEvent(self, widget, event): 
        if self.injector != None:
            if self.injector.isRunning():
                self.injector.terminate()
        if self.faultsEdited:
            msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Faults have been edited. Do you want to save faults?")
            msgDlg.add_button("Cancel", gtk.RESPONSE_CLOSE)
            res = msgDlg.run()
            if res == gtk.RESPONSE_CLOSE:
                msgDlg.destroy()
                return True
            if res == gtk.RESPONSE_YES:
                self.save(widget)
                msgDlg.destroy()
            msgDlg.destroy()
        return False
    
    # obsluha radioButtonu v tabulce v pokrocilem rezimu
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
            self.procfsWriter(selValue, faultList.get_value(row, 7))
        else:
            self.faultsStartValue[selValue] = "NOFAULT"
            self.procfsWriter(selValue, "NOFAULT")
        faultList.set(row, 8, selected)
        
    # aplikace se prepne do zakladniho modu
    def modeBasicToggled(self, widget):
        if widget.get_active():
            if self.faultsEdited:
                msgDlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO, message_format="Faults have been edited. Do you want to save faults?")
                res = msgDlg.run()
                if res == gtk.RESPONSE_YES:
                    self.save(widget)
                msgDlg.destroy()
            self.faultsEdited = False
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
            

    # aplikace se prepne do pokrocileho modu (rezimu)    
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
    
    # prida text do Logu
    def addTextToLog(self, text):
        self.logText += text
        self.textBuffer.set_text(self.logText)
        
    # zajisti aby Log byl scrolovany vzdy dole
    # abychom videli posledni pridany zaznam
    def scrollDown(self, widget, e):
        scrolled = self.builder.get_object("scrolledwindowLog")
        adj = scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        scrolled.set_vadjustment(adj)

    # povoli, zadaze odpovidajici chybu
    # zapise do souboru v procfs
    def procfsWriter(self, name, value):
        if self.moduleName != "":
            os.system("echo " + str(value) + " > /proc/systemtap/" + self.moduleName + "/" + name)
       
       
    # metody pro radioButtony s chybami
    # v zakladnim rezimu prace
       
    # File management
    def nofileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "NOFAULT"
            self.procfsWriter("file", "NOFAULT")

    def eacessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EACCES"
            self.procfsWriter("file", "EACCES")

    def enoentRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "ENOENT"
            self.procfsWriter("file", "ENOENT")
    
    def emfileRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EMFILE"
            self.procfsWriter("file", "EMFILE")
    
    def fileENOTDIRRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "ENOTDIR"
            self.procfsWriter("file", "ENOTDIR")
    
    def fileEBUSYRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EBUSY"
            self.procfsWriter("file", "EBUSY")
    
    def fileENOTEMPTYRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "ENOTEMPTY"
            self.procfsWriter("file", "ENOTEMPTY")
    
    def fileEMLINKRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EMLINK"
            self.procfsWriter("file", "EMLINK")
    
    def ewouldblockRadioClicked(self, widget):
        if widget.get_active():
            pass
        else:
            pass
    
    def eexistRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["file"] = "EEXIST"
            self.procfsWriter("file", "EEXIST")
    
    # Network
    def nonetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "NOFAULT"
            self.procfsWriter("net", "NOFAULT")

    def enetunreachRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENETUNREACH"
            self.procfsWriter("net", "ENETUNREACH")
    
    def etimedoutRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ETIMEDOUT"
            self.procfsWriter("net", "ETIMEDOUT")
    
    def econnrefusedRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNREFUSED"
            self.procfsWriter("net", "ECONNREFUSED")
    
    def econnresetRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ECONNRESET"
            self.procfsWriter("net", "ECONNRESET")
    
    def emsgsizeRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EMSGSIZE"
            self.procfsWriter("net", "EMSGSIZE")
    
    def eisconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "EISCONN"
            self.procfsWriter("net", "EISCONN")
    
    def enotconnRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["net"] = "ENOTCONN"
            self.procfsWriter("net", "ENOTCONN")

    # Process
    def noprocessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "NOFAULT"
            self.procfsWriter("process", "NOFAULT")

    def eaccesProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "EACCES"
            self.procfsWriter("process", "EACCES")

    def enoentProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOENT"
            self.procfsWriter("process", "ENOENT")

    def enoexecRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOEXEC"
            self.procfsWriter("process", "ENOEXEC")

    def enomemProcessRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ENOMEM"
            self.procfsWriter("process", "ENOMEM")

    def elibbadRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ELIBBAD"
            self.procfsWriter("process", "ELIBBAD")

    def etxtbsyRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["process"] = "ETXTBSY"
            self.procfsWriter("process", "ETXTBSY")
            
    # Memory
    def noMemoryRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["memory"] = "NOFAULT"
            self.procfsWriter("memory", "NOFAULT")
            
    def memoryEnomemRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["memory"] = "ENOMEM"
            self.procfsWriter("memory", "ENOMEM")
            
    def memoryEaccesRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["memory"] = "EACCES"
            self.procfsWriter("memory", "EACCES")
            
    def memoryEagainRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["memory"] = "EAGAIN"
            self.procfsWriter("memory", "EGAIN")
            
    # rw
    def noRwRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["rw"] = "NOFAULT"
            self.procfsWriter("rw", "NOFAULT")
        
    def rwEbadfRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["rw"] = "EBADF"
            self.procfsWriter("rw", "EBADF")
        
    def rwEioRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["rw"] = "EIO"
            self.procfsWriter("rw", "EIO")
        
    def rwEfbigRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["rw"] = "EFBIG"
            self.procfsWriter("rw", "EFBIG")
        
    def rwEnospcRadioClicked(self, widget):
        if widget.get_active():
            self.enableFault["rw"] = "ENOSPC"
            self.procfsWriter("rw", "ENOSPC")
        
            
if __name__ == "__main__":
    #sender = SenderStart()
    app = TutorialApp()
    try:
        gtk.main()
    except KeyboardInterrupt:
        app.keyboardInterrupt()



