#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Soubor: FaultDialog.py
# Popis:  Dialog pro pridavani chyb v pokrocilem modu
# Autor:  Martin Zelinka, xzelin12@stud.fit.vutbr.cz

import pygtk
pygtk.require("2.0")
import gtk
import gobject

# Dialog pro pridani novych chyb v pokrocilem rezimu
class FaultDialog():

    # syscallsAndErrors - seznam vsech systemovych volani a 
    # navratovych hodnot
    def __init__(self, syscallsAndErrors):
        self.syscallsAndErrors = syscallsAndErrors
        syscalls = []
        for key in syscallsAndErrors[0].keys():
            syscalls.append(key)
        syscalls.sort()
        self.count = len(syscalls)
        self.list = gtk.ListStore(gobject.TYPE_STRING)
        for s in syscalls:
            self.list.append([s])
        self.builder = gtk.Builder()
        self.builder.add_from_file("fault_dialog.glade")
        self.builder.connect_signals({"syscallsComboboxChanged": self.syscallsComboboxChanged, "cancelButtonClicked" : self.cancelButtonClicked, "addButtonClicked" : self.addButtonClicked, "faultDialogClose" : self.faultDialogClose})
        
    # spusteni dialogu
    # existedFaults - chyby, ktere jiz byli pridany
    def run(self, existedFaults):
        self.existedFaults = existedFaults
        self.dlg = self.builder.get_object("faultDialog")
        self.addButton = self.builder.get_object("addButton")
        self.addButton.set_sensitive(False)
        
        # nastaveni comboboxu se systemovymi volanimi
        self.syscallsCombobox = self.builder.get_object("syscallsCombobox")
        self.syscallsCombobox.set_model(self.list)
        cell = gtk.CellRendererText()
        self.syscallsCombobox.pack_start(cell, True)
        self.syscallsCombobox.add_attribute(cell, "text", 0)
        if self.count > 50:
            self.syscallsCombobox.set_wrap_width(5)
        self.counterTrue = 0
        
        # Vytvoreni seznamu pro chyby
        self.errorView = self.builder.get_object("errorTreeview")
        self.errorList = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.errorView.set_model(self.errorList)
        cell = gtk.CellRendererToggle()
        cell.connect("toggled", self.errorToggled, self.errorList)
        column = gtk.TreeViewColumn("Select", cell, active=0)
        column.set_clickable(True)
        self.errorView.append_column(column)
        column = gtk.TreeViewColumn("Errors", gtk.CellRendererText(), text=1)
        self.errorView.append_column(column)
        column = gtk.TreeViewColumn("Desription", gtk.CellRendererText(), text=2)
        self.errorView.append_column(column)
        
        
        self.returnValue = (False, None)
        self.dlg.run()
        return self.returnValue
        
    # obsluha checkboxu u chyb
    def errorToggled(self, widget, index, errorList):
        row = errorList.get_iter((int(index),))
        selected = errorList.get_value(row, 0)

        selected = not selected
        if selected:
            self.counterTrue += 1
            self.addButton.set_sensitive(True)
        else:
            self.counterTrue -= 1
            if self.counterTrue == 0:
                self.addButton.set_sensitive(False)
        errorList.set(row, 0, selected)

    # reakce na zmenu comboboxu
    def syscallsComboboxChanged(self, widget):
        syscallsModel = widget.get_model()
        index = widget.get_active()
        self.selectedSyscall = syscallsModel[index][0]
        self.errorList.clear()
        for e in self.syscallsAndErrors[0][syscallsModel[index][0]]:
            if [self.selectedSyscall, e] not in self.existedFaults:
                self.errorList.append([False, e, self.syscallsAndErrors[2][e]])
        
    # ukonceni dialogu
    def faultDialogClose(self, widget, response):
        self.dlg.hide()
            
    # ukonceni tlacitkem cancel
    def cancelButtonClicked(self, widget):
        self.dlg.destroy()

    # pridani novych chyb - tlacitko Add
    def addButtonClicked(self, widget):
        errors = []
        row = self.errorList.get_iter_first()
        while row != None:
            selected = self.errorList.get_value(row, 0)
            if selected:
                errors.append(self.errorList.get_value(row, 1))
            row = self.errorList.iter_next(row)
        args = []
        arg1 = self.builder.get_object("arg1Entry")
        args.append(arg1.get_text())
        arg2 = self.builder.get_object("arg2Entry")
        args.append(arg2.get_text())
        arg3 = self.builder.get_object("arg3Entry")
        args.append(arg3.get_text())
        arg4 = self.builder.get_object("arg4Entry")
        args.append(arg4.get_text())
        arg5 = self.builder.get_object("arg5Entry")
        args.append(arg5.get_text())
        arg6 = self.builder.get_object("arg6Entry")
        args.append(arg6.get_text())
        self.returnValue = (True, (self.selectedSyscall, errors, args))
        self.dlg.destroy()
        
        
