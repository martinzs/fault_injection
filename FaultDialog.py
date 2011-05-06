#!/usr/bin/env python


import pygtk
pygtk.require("2.0")
import gtk
import gobject


class FaultDialog():
    def __init__(self, syscallsAndErrors):
        self.syscallsAndErrors = syscallsAndErrors
        syscalls = []
        for key in syscallsAndErrors[0].keys():
            syscalls.append(key)
        syscalls.sort()
        self.list = gtk.ListStore(gobject.TYPE_STRING)
        for s in syscalls:
            self.list.append([s])
        self.builder = gtk.Builder()
        self.builder.add_from_file("fault_dialog.glade")
        self.builder.connect_signals({"syscallsComboboxChanged": self.syscallsComboboxChanged, "cancelButtonClicked" : self.cancelButtonClicked, "addButtonClicked" : self.addButtonClicked, "faultDialogClose" : self.faultDialogClose})
        
    def run(self, existedFaults):
        self.existedFaults = existedFaults
        self.dlg = self.builder.get_object("faultDialog")
        self.addButton = self.builder.get_object("addButton")
        self.addButton.set_sensitive(False)
        
        self.syscallsCombobox = self.builder.get_object("syscallsCombobox")
        self.syscallsCombobox.set_model(self.list)
        cell = gtk.CellRendererText()
        self.syscallsCombobox.pack_start(cell, True)
        self.syscallsCombobox.add_attribute(cell, "text", 0)
        self.counterTrue = 0
        
        # List of errors
        self.errorView = self.builder.get_object("errorTreeview")
        self.errorList = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.errorView.set_model(self.errorList)
        column = gtk.TreeViewColumn("Errors", gtk.CellRendererText(), text=0)
        self.errorView.append_column(column)
        cell = gtk.CellRendererToggle()
        cell.connect("toggled", self.errorToggled, self.errorList)
        column = gtk.TreeViewColumn("Select", cell, active=1)
        column.set_clickable(True)
        self.errorView.append_column(column)
        
        self.returnValue = (False, None)
        self.dlg.run()
        #self.dlg.show()
        return self.returnValue
        
    def errorToggled(self, widget, index, errorList):
        row = errorList.get_iter((int(index),))
        selected = errorList.get_value(row, 1)

        selected = not selected
        if selected:
            self.counterTrue += 1
            self.addButton.set_sensitive(True)
        else:
            self.counterTrue -= 1
            if self.counterTrue == 0:
                self.addButton.set_sensitive(False)
        errorList.set(row, 1, selected)


    def syscallsComboboxChanged(self, widget):
        syscallsModel = widget.get_model()
        index = widget.get_active()
        self.selectedSyscall = syscallsModel[index][0]
        print syscallsModel[index][0]
        self.errorList.clear()
        for e in self.syscallsAndErrors[0][syscallsModel[index][0]]:
            if [self.selectedSyscall, e] not in self.existedFaults:
                self.errorList.append([e, False])
        
        
    def faultDialogClose(self, widget, response):
        print "konec"
        self.dlg.hide()
            
    def cancelButtonClicked(self, widget):
        self.dlg.destroy()

        
    def addButtonClicked(self, widget):
        errors = []
        row = self.errorList.get_iter_first()
        while row != None:
            selected = self.errorList.get_value(row, 1)
            if selected:
                errors.append(self.errorList.get_value(row, 0))
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
        
        
